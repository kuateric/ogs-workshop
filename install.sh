#!/usr/bin/env bash
# OGS Workshop Ubuntu 24.04/26.04 (x86_64): system prerequisites, Intel oneAPI MKL
# (PARDISO), TFEL/MFront, full OGS source build, Python tools and desktop apps.
# Does NOT modify the user's existing OGS installations or delete anything.
set -Eeuo pipefail
umask 022

HERE="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
ROOT="${OGS_WORKSHOP_HOME:-$HOME/ogs-workshop}"
SRC="$ROOT/src/ogs"
BUILD="$ROOT/build/ogs"
PREFIX="$ROOT/install/ogs"
TFEL_SRC="$ROOT/src/tfel"
TFEL_BUILD="$ROOT/build/tfel"
TFEL_PREFIX="$ROOT/install/tfel"
TOOLS_VENV="$ROOT/.build-tools"
PYTHON_VERSION="3.12"
VENV="$ROOT/.venv"
OGS_COMMIT="${OGS_WORKSHOP_OGS_COMMIT:-8ffec079b9ce8764ab565c6470839b34033bc718}"
TFEL_REF="${OGS_WORKSHOP_TFEL_REF:-rliv-5.1}"
JOBS="${OGS_WORKSHOP_JOBS:-2}"
MODE="${1:---help}"
MKLROOT=""
OMP_LIB=""
CM=""

usage() {
  cat <<EOF
OGS Workshop Installer - Ubuntu 24.04/26.04 x86_64

Usage:
  bash install.sh --all        System + Intel oneAPI/PARDISO + MFront + OGS +
                               Python analysis + ParaView + VS Code + smoke tests
  bash install.sh --system     Ubuntu build prerequisites (requires sudo)
  bash install.sh --intel      Intel oneAPI Toolkit 2026 / MKL / PARDISO (sudo)
  bash install.sh --tfel       Build TFEL 5.1 / MFront in user directory
  bash install.sh --ogs        Build complete upstream OGS with MKL/MFront
  bash install.sh --gmsh       Install Gmsh CLI/GUI and mesh-generation prerequisites (sudo)
  bash install.sh --python     Install evaluation packages in a private venv
  bash install.sh --desktop    Install ParaView and VS Code (requires sudo)
  bash install.sh --verify     Check installed dependencies and run Python checks
  bash install.sh --smoke      Run small real OGS calculations, save JSON report
  bash install.sh --dry-run    Print planned paths/commands only
  bash install.sh --help       Show this help

This installer is ADDITIVE and idempotent. It NEVER deletes previous OGS,
Intel, SSH, Tailscale, or user directories. No automatic OGS rebuild in --verify.
Default directory: $ROOT
Change path: OGS_WORKSHOP_HOME=/path/to/workshop
For colleagues: at least 60 GiB free disk and 16 GiB RAM recommended.
For a source build expect a long compilation, especially for VTK.
EOF
}
case "$MODE" in
  --all|--system|--intel|--tfel|--ogs|--gmsh|--python|--desktop|--verify|--smoke|--dry-run|--help|-h) ;;
  *) usage; echo "Unknown option: $MODE" >&2; exit 2 ;;
esac
if [[ "$MODE" == --help || "$MODE" == -h ]]; then usage; exit 0; fi

if [[ ! -f /etc/os-release ]]; then echo "Missing /etc/os-release" >&2; exit 1; fi
# shellcheck source=/dev/null
source /etc/os-release
if [[ "${ID:-}" != ubuntu || ( "${VERSION_ID:-}" != 24.04 && "${VERSION_ID:-}" != 26.04 ) || "$(uname -m)" != x86_64 ]]; then
  echo "Supported target is Ubuntu 24.04/26.04 x86_64; detected ${PRETTY_NAME:-unknown} $(uname -m)." >&2
  exit 2
fi
[[ "$(id -u)" -ne 0 ]] || { echo "Run as regular user, not as root. sudo is used for apt." >&2; exit 2; }
[[ "$JOBS" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid OGS_WORKSHOP_JOBS: $JOBS" >&2; exit 2; }
if [[ "$ROOT" == / || "$ROOT" == "$HOME" ]]; then echo "Unsafe workspace: $ROOT" >&2; exit 2; fi
mkdir -p "$ROOT/logs"
exec 9>"$ROOT/logs/install.lock"
if ! flock -n 9; then echo "Another workshop install is running (install.lock)." >&2; exit 75; fi
LOG="$ROOT/logs/install-$(date -u +%Y%m%dT%H%M%SZ).log"
exec > >(tee -a "$LOG") 2>&1
trap 'rc=$?; echo "[FAIL] line=$LINENO exit=$rc log=$LOG" >&2; exit "$rc"' ERR
echo "[workshop] mode=$MODE root=$ROOT jobs=$JOBS"
echo "[workshop] log=$LOG"

sudo_check() {
  command -v sudo >/dev/null || { echo "sudo required for system packages" >&2; return 1; }
  sudo -v
}
available() { command -v "$1" >/dev/null 2>&1; }
logstep() { echo; echo "===== $* ====="; }
ensure_tools() {
  if [[ ! -x "$TOOLS_VENV/bin/cmake" ]]; then
    python3 -m venv "$TOOLS_VENV"
    "$TOOLS_VENV/bin/python" -m pip install --upgrade 'pip<27' 'cmake==3.31.10'
  fi
  CM="$TOOLS_VENV/bin/cmake"
  "$CM" --version | head -1
}
detect_mkl() {
  local candidate
  for candidate in "$HOME/intel/oneapi/mkl/latest" /opt/intel/oneapi/mkl/latest; do
    if [[ -f "$candidate/include/mkl.h" && -f "$candidate/lib/libmkl_rt.so" ]]; then
      MKLROOT="$candidate"
      break
    fi
  done
  [[ -n "$MKLROOT" ]] || return 1
  for candidate in \
    "$HOME/intel/oneapi/compiler/2026.2/lib" \
    /opt/intel/oneapi/compiler/2026.2/lib \
    /opt/intel/oneapi/compiler/latest/lib \
    "$HOME/intel/oneapi/compiler/latest/lib"; do
    if [[ -f "$candidate/libiomp5.so" ]]; then OMP_LIB="$candidate"; break; fi
  done
  if [[ -z "$OMP_LIB" ]]; then
    local found
    found="$(find "$HOME/intel/oneapi" /opt/intel/oneapi -name libiomp5.so -print -quit 2>/dev/null || true)"
    if [[ -n "$found" ]]; then OMP_LIB="$(dirname "$found")"; fi
  fi
  [[ -n "$OMP_LIB" ]] || { echo "Intel OpenMP runtime libiomp5.so missing; install Intel oneAPI Toolkit." >&2; return 1; }
  echo "[intel] MKLROOT=$MKLROOT OMP_LIB=$OMP_LIB"
}
export_runtime() {
  detect_mkl
  export MKLROOT OMP_LIB
  export TFELHOME="$TFEL_PREFIX"
  export PATH="$PREFIX/bin:$TFEL_PREFIX/bin:$PATH"
  export LD_LIBRARY_PATH="$PREFIX/lib:$BUILD/lib:$MKLROOT/lib:$OMP_LIB:$TFEL_PREFIX/lib:$TFEL_PREFIX/lib64:${LD_LIBRARY_PATH:-}"
  export CMAKE_PREFIX_PATH="$TFEL_PREFIX:$MKLROOT:${CMAKE_PREFIX_PATH:-}"
  export OGS_BIN_PATH="$PREFIX/bin"
  export CPM_SOURCE_CACHE="$ROOT/cache/cpm"
  mkdir -p "$CPM_SOURCE_CACHE"
}
install_system() {
  logstep "Ubuntu build prerequisites and graphics libraries"
  sudo_check
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential g++ gfortran git ninja-build cmake ccache curl wget \
    ca-certificates unzip xz-utils file rsync pkg-config gnupg \
    python3 python3-dev python3-pip python3-venv python3-numpy pybind11-dev \
    libhdf5-dev libxml2-dev zlib1g-dev libeigen3-dev libboost-all-dev \
    libblas-dev liblapack-dev libgl1 libglu1-mesa libxrender1 libxext6 \
    libx11-xcb1 libxcb-cursor0 libxkbcommon-x11-0
  ensure_tools
}
install_gmsh() {
  logstep "Gmsh mesh generator (Ubuntu APT CLI + GUI)"
  sudo_check
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y gmsh libgmsh-dev
  command -v gmsh >/dev/null
  gmsh --version
  echo "[PASS] Gmsh executable installed"
}
install_intel() {
  logstep "Intel oneAPI Toolkit incl. oneMKL 2026 and PARDISO"
  if detect_mkl; then echo "[SKIP] Intel MKL and Intel OpenMP already installed"; return 0; fi
  sudo_check
  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf -- "$tmp"' RETURN
  curl --fail --location --retry 3 --silent --show-error \
    https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB \
    -o "$tmp/intel.asc"
  gpg --batch --dearmor -o "$tmp/intel.gpg" "$tmp/intel.asc"
  sudo install -m 0644 "$tmp/intel.gpg" /usr/share/keyrings/oneapi-archive-keyring.gpg
  printf '%s\n' \
    'deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main' \
    | sudo tee /etc/apt/sources.list.d/oneapi.list >/dev/null
  sudo apt-get update
  # 2026 combined Base/HPC toolkit contains MKL development + Intel OpenMP.
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y intel-oneapi-toolkit
  trap - RETURN
  rm -rf -- "$tmp"
  detect_mkl || { echo "Intel oneAPI installed but MKL or Intel OpenMP cannot be found." >&2; return 1; }
}
test_pardiso() {
  logstep "Numerical Intel PARDISO smoke: solve A x = b, expect x=(2,2)"
  export_runtime
  cat > "$ROOT/logs/pardiso_check.c" <<'C'
#include <mkl.h>
#include <math.h>
#include <stdio.h>
int main(void) {
  void *pt[64]={0}; MKL_INT iparm[64]={0},perm[2]={0};
  MKL_INT n=2,maxfct=1,mnum=1,mtype=11,nrhs=1,msglvl=0,error=0,phase=13;
  MKL_INT ia[]={1,2,3},ja[]={1,2};
  double a[]={2.,4.},b[]={4.,8.},x[]={0.,0.};
  pardiso(pt,&maxfct,&mnum,&mtype,&phase,&n,a,ia,ja,perm,
          &nrhs,iparm,&msglvl,b,x,&error);
  printf("PARDISO_solution=(%.12g,%.12g) error=%d\n",x[0],x[1],(int)error);
  int ok=(error==0 && fabs(x[0]-2.)<1.e-9 && fabs(x[1]-2.)<1.e-9);
  phase=-1; pardiso(pt,&maxfct,&mnum,&mtype,&phase,&n,a,ia,ja,perm,
                    &nrhs,iparm,&msglvl,b,x,&error);
  return (ok && error==0)?0:1;
}
C
  gcc "$ROOT/logs/pardiso_check.c" -I"$MKLROOT/include" -L"$MKLROOT/lib" \
    -L"$OMP_LIB" -Wl,-rpath,"$MKLROOT/lib" -Wl,-rpath,"$OMP_LIB" \
    -Wl,--no-as-needed -lmkl_rt -liomp5 -lm -Wl,--as-needed \
    -lpthread -ldl -o "$ROOT/logs/pardiso_check"
  MKL_NUM_THREADS=2 "$ROOT/logs/pardiso_check"
  echo "[PASS] Intel oneMKL PARDISO numerical solve"
}
install_tfel() {
  logstep "TFEL/MFront stable 5.1 branch - build from source"
  ensure_tools
  if [[ -x "$TFEL_PREFIX/bin/mfront" && -x "$TFEL_PREFIX/bin/tfel-config" ]]; then
    export LD_LIBRARY_PATH="$TFEL_PREFIX/lib:$TFEL_PREFIX/lib64:${LD_LIBRARY_PATH:-}"
    "$TFEL_PREFIX/bin/mfront" --version >/dev/null
    "$TFEL_PREFIX/bin/tfel-config" --version >/dev/null
    echo "[SKIP] TFEL/MFront already installed and runnable: $TFEL_PREFIX"
    return 0
  fi
  mkdir -p "$ROOT/src" "$ROOT/build" "$ROOT/install"
  if [[ ! -d "$TFEL_SRC/.git" ]]; then
    [[ ! -e "$TFEL_SRC" ]] || { echo "Source exists but is not git: $TFEL_SRC" >&2; return 1; }
    git clone --depth 1 --branch "$TFEL_REF" https://github.com/thelfer/tfel.git "$TFEL_SRC"
  fi
  "$CM" -S "$TFEL_SRC" -B "$TFEL_BUILD" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$TFEL_PREFIX" \
    -DTFEL_APPEND_VERSION=OFF -Denable-python-bindings=OFF \
    -Denable-website=OFF
  "$CM" --build "$TFEL_BUILD" --parallel "$JOBS"
  "$CM" --install "$TFEL_BUILD"
  test -x "$TFEL_PREFIX/bin/mfront"
  test -x "$TFEL_PREFIX/bin/tfel-config"
  git -C "$TFEL_SRC" rev-parse HEAD > "$ROOT/logs/tfel-git-sha.txt"
  # Standalone TFEL commands need their installed shared libraries on the loader path.
  # The full OGS runtime environment is not available yet during a fresh --tfel stage.
  export LD_LIBRARY_PATH="$TFEL_PREFIX/lib:$TFEL_PREFIX/lib64:${LD_LIBRARY_PATH:-}"
  "$TFEL_PREFIX/bin/mfront" --version
  "$TFEL_PREFIX/bin/tfel-config" --version
}
install_ogs() {
  logstep "Official OGS: all processes + Intel MKL/PARDISO + MFront"
  ensure_tools
  export_runtime
  [[ -x "$TFEL_PREFIX/bin/mfront" ]] || { echo "Run --tfel first" >&2; return 1; }
  test_pardiso
  if [[ -x "$PREFIX/bin/ogs" && -f "$PREFIX/BUILD_COMMIT.txt" ]] &&
     [[ "$(cat "$PREFIX/BUILD_COMMIT.txt")" == "$OGS_COMMIT" ]]; then
    "$PREFIX/bin/ogs" --help >/dev/null
    echo "[SKIP] pinned OGS binary already installed: $OGS_COMMIT"
    return 0
  fi
  mkdir -p "$ROOT/src" "$ROOT/build" "$ROOT/install"
  # Download just the pinned commit. Avoid partial-clone filters because
  # interrupted lazy blob downloads can fail during checkout.
  if [[ ! -d "$SRC/.git" ]]; then
    [[ ! -e "$SRC" ]] || { echo "Source exists but is not git: $SRC" >&2; return 1; }
    mkdir -p "$SRC"
    git -C "$SRC" init
    git -C "$SRC" remote add origin https://gitlab.opengeosys.org/ogs/ogs.git
  fi
  [[ "$(git -C "$SRC" remote get-url origin)" == https://gitlab.opengeosys.org/ogs/ogs.git ]] ||
    { echo "Unexpected OGS upstream remote" >&2; return 1; }
  # Repair settings from an earlier interrupted partial clone without
  # deleting the source folder or unrelated installation directories.
  git -C "$SRC" config --unset-all remote.origin.partialclonefilter || true
  git -C "$SRC" config --unset-all remote.origin.promisor || true
  local attempt max_attempts=5 delay_seconds
  for ((attempt=1; attempt<=max_attempts; attempt++)); do
    echo "[OGS download] Fetching pinned commit, attempt $attempt/$max_attempts"
    if git -c http.version=HTTP/1.1 \
           -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=120 \
           -C "$SRC" fetch --no-filter --depth 1 origin "$OGS_COMMIT" &&
       git -C "$SRC" -c advice.detachedHead=false checkout --detach --force "$OGS_COMMIT" &&
       git -C "$SRC" fsck --connectivity-only --no-reflogs >/dev/null; then
      echo "[PASS] OGS source downloaded and checked out: $OGS_COMMIT"
      break
    fi
    if ((attempt == max_attempts)); then
      echo "[FAIL] OGS download failed after $max_attempts attempts. Check network access and rerun 'bash install'." >&2
      return 1
    fi
    delay_seconds=$((attempt * 10))
    echo "[WARN] Interrupted OGS download. Retrying in ${delay_seconds}s; preserving the working directory."
    sleep "$delay_seconds"
  done
  git -C "$SRC" rev-parse HEAD | tee "$ROOT/logs/ogs-git-sha.txt"
  [[ -d "$SRC/ProcessLib/TH2M" && -d "$SRC/ProcessLib/ThermoRichardsMechanics" ]]
  "$CM" -S "$SRC" -B "$BUILD" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$PREFIX" \
    -DCPM_SOURCE_CACHE:PATH="$CPM_SOURCE_CACHE" \
    -DHDF5_ROOT:PATH=/usr/lib/x86_64-linux-gnu/hdf5/serial \
    -DHDF5_PREFER_PARALLEL:BOOL=OFF \
    -DOGS_BUILD_CLI:BOOL=ON -DOGS_BUILD_GUI:BOOL=OFF \
    -DOGS_BUILD_UTILS:BOOL=ON -DOGS_BUILD_PROCESSES=ON \
    -DOGS_BUILD_TESTING:BOOL=OFF -DBUILD_TESTING:BOOL=OFF \
    -DOGS_USE_MFRONT:BOOL=ON -DOGS_USE_MKL:BOOL=ON \
    -DOGS_EIGEN_PARALLEL_BACKEND=MKL \
    -DOGS_USE_XDMF:BOOL=ON -DBUILD_SHARED_LIBS:BOOL=ON
  grep -Eq '^OGS_USE_MKL:BOOL=ON$' "$BUILD/CMakeCache.txt"
  grep -Eq '^OGS_USE_MFRONT:BOOL=ON$' "$BUILD/CMakeCache.txt"
  "$CM" --build "$BUILD" --parallel "$JOBS"
  [[ -x "$BUILD/bin/ogs" ]]
  mkdir -p "$PREFIX/bin" "$PREFIX/lib"
  # Upstream CMake install target may not package all utility executables.
  "$CM" --install "$BUILD" --prefix "$PREFIX"
  if [[ -d "$BUILD/bin" ]]; then cp -a "$BUILD/bin/." "$PREFIX/bin/"; fi
  if [[ -d "$BUILD/lib" ]]; then cp -a "$BUILD/lib/." "$PREFIX/lib/"; fi
  [[ -x "$PREFIX/bin/ogs" ]]
  export_runtime
  "$PREFIX/bin/ogs" --help >/dev/null
  echo "$OGS_COMMIT" > "$PREFIX/BUILD_COMMIT.txt"
  echo "[PASS] Full OGS build: $PREFIX/bin/ogs"
}
install_python() {
  logstep "Python workshop: venv + OGSTools + ogs6py + VTUinterface + analysis"
  [[ -f "$HERE/requirements.txt" ]] || { echo "Missing sibling requirements.txt" >&2; return 1; }
  if [[ -x "$VENV/bin/python" ]]; then
    existing_version="$("$VENV/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    [[ "$existing_version" == "$PYTHON_VERSION" ]] || { echo "Existing venv uses Python $existing_version, expected $PYTHON_VERSION" >&2; return 1; }
  else
    ensure_tools
    "$TOOLS_VENV/bin/python" -m pip install "uv>=0.9,<1"
    "$TOOLS_VENV/bin/uv" python install "$PYTHON_VERSION"
    "$TOOLS_VENV/bin/uv" venv --python "$PYTHON_VERSION" "$VENV"
  fi
  "$VENV/bin/python" -m pip install --upgrade 'pip<27'
  "$VENV/bin/python" -m pip install -r "$HERE/requirements.txt"
  "$VENV/bin/python" -m pip check
  "$VENV/bin/python" -m ipykernel install --user --name ogs-workshop \
    --display-name 'Python (OGS Workshop)'
  mkdir -p "$ROOT/notebooks"
  for notebook in "$HERE"/notebooks/*.ipynb; do
    [[ -f "$notebook" ]] || continue
    if [[ ! -e "$ROOT/notebooks/$(basename "$notebook")" ]]; then
      cp -- "$notebook" "$ROOT/notebooks/"
    fi
  done
  echo "[PASS] Python environment: $VENV/bin/python"
}
install_desktop() {
  logstep "ParaView (Ubuntu package) and Visual Studio Code (Microsoft signed APT)"
  sudo_check
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y paraview
  if ! available code; then
    local tmp
    tmp="$(mktemp -d)"
    trap 'rm -rf -- "$tmp"' RETURN
    curl --fail --location --retry 3 --silent --show-error \
      https://packages.microsoft.com/keys/microsoft.asc -o "$tmp/ms.asc"
    gpg --batch --dearmor -o "$tmp/ms.gpg" "$tmp/ms.asc"
    sudo install -m 0644 "$tmp/ms.gpg" /usr/share/keyrings/microsoft.gpg
    cat > "$tmp/vscode.sources" <<'EOF'
Types: deb
URIs: https://packages.microsoft.com/repos/code
Suites: stable
Components: main
Architectures: amd64
Signed-By: /usr/share/keyrings/microsoft.gpg
EOF
    sudo install -m 0644 "$tmp/vscode.sources" /etc/apt/sources.list.d/vscode.sources
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y code
    trap - RETURN
    rm -rf -- "$tmp"
  fi
  command -v paraview
  command -v code
  echo "[PASS] Desktop packages installed"
}
write_env() {
  logstep "Write portable workshop activation environment"
  export_runtime
  cat > "$ROOT/activate.sh" <<EOF
#!/usr/bin/env bash
# Source this file: source "$ROOT/activate.sh"
if [[ -f "$VENV/bin/activate" ]]; then source "$VENV/bin/activate"; fi
export MKLROOT="$MKLROOT"
export TFELHOME="$TFEL_PREFIX"
export PATH="$PREFIX/bin:$TFEL_PREFIX/bin:\$PATH"
export LD_LIBRARY_PATH="$PREFIX/lib:$BUILD/lib:$MKLROOT/lib:$OMP_LIB:$TFEL_PREFIX/lib:$TFEL_PREFIX/lib64:\${LD_LIBRARY_PATH:-}"
export OGS_BIN_PATH="$PREFIX/bin"
EOF
  chmod 0644 "$ROOT/activate.sh"
  printf '%s\n' "Source the workshop env: source '$ROOT/activate.sh'"
}
verify() {
  logstep "Verifying core and numerical PARDISO"
  export_runtime
  test_pardiso
  test -x "$TFEL_PREFIX/bin/mfront"
  "$TFEL_PREFIX/bin/mfront" --version
  test -x "$TFEL_PREFIX/bin/tfel-config"
  "$TFEL_PREFIX/bin/tfel-config" --version
  test -x "$PREFIX/bin/ogs"
  "$PREFIX/bin/ogs" --help >/dev/null
  # Check desktop applications without launching GUI in a headless SSH session.
  for app in gmsh paraview code; do
    command -v "$app" >/dev/null || {
      echo "Missing GUI package: $app (run --desktop)" >&2; return 1;
    }
    echo "[PASS] Desktop binary present: $app ($(command -v "$app"))"
  done
  [[ -x "$VENV/bin/python" ]] || { echo "Run --python first" >&2; return 1; }
  "$VENV/bin/python" "$HERE/verify.py" --packages --ogs "$PREFIX/bin/ogs" \
    --source "$SRC/Tests/Data" --output "$ROOT/results"
  echo "[PASS] Workshop verification"
}
smoke() {
  export_runtime
  [[ -x "$VENV/bin/python" ]] || { echo "Run --python first" >&2; return 1; }
  "$VENV/bin/python" "$HERE/verify.py" --packages --models --ogs "$PREFIX/bin/ogs" \
    --source "$SRC/Tests/Data" --output "$ROOT/results"
}

case "$MODE" in
  --system) install_system ;;
  --intel) install_intel; test_pardiso ;;
  --tfel) install_tfel ;;
  --ogs) install_ogs; write_env ;;
  --gmsh) install_gmsh ;;
  --python) install_python ;;
  --desktop) install_desktop ;;
  --verify) verify ;;
  --smoke) smoke ;;
  --all)
    install_system
    install_gmsh
    install_intel
    test_pardiso
    install_tfel
    install_ogs
    install_python
    install_desktop
    write_env
    verify
    smoke
    ;;
  --dry-run)
    printf '%s\n' \
      "OS: Ubuntu 24.04/26.04 x86_64" \
      "WORKSHOP_ROOT=$ROOT" \
      "OGS_PIN=$OGS_COMMIT" \
      "TFEL_REF=$TFEL_REF" \
      "OGS_INSTALL=$PREFIX" \
      "TFEL_INSTALL=$TFEL_PREFIX" \
      "PYTHON_VENV=$VENV" \
      "INTEL_ONEAPI=system apt Intel oneAPI toolkit incl. MKL+OpenMP" \
      "GMSH=apt gmsh + libgmsh-dev; Python gmsh API in venv" \
      "DESKTOP=apt paraview + signed Microsoft repo code" \
      "MODIFIES_EXISTING_OGS=no" \
      "DELETES_EXISTING_DIRECTORIES=no"
    ;;
esac
echo "[SUCCESS] mode=$MODE"
