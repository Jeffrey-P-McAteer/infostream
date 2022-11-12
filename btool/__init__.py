
import os
import stat
import sys
import subprocess
import shutil
import traceback
import shelve

ENV_D = {}

def main(args=sys.argv):
  global ENV_D
  move_to_repo_root()
  ENV_D = read_env()
  try:

    build_desktop_x86_64_unknown_linux_gnu()
    build_desktop_x86_64_pc_windows_gnu()
    build_desktop_x86_64_apple_darwin()

  except:
    traceback.print_exc()

    # For any failures, skip our optimistic approaches
    ENV_D['nozig'] = True

  save_env(ENV_D)

def read_env():
  env_d = {}
  if os.path.exists('.btool.env'):
    try:
      with shelve.open('.btool.env') as d:
        env_d.update(d)
    except:
      pass
  return env_d

def save_env(env_d):
  with shelve.open('.btool.env') as d:
    d.update(env_d)

def move_to_repo_root():
  for i in range(0, 99):
    if not os.path.exists('readme.md'):
      os.chdir('..')

def make_f_executable(file):
  st = os.stat(file)
  os.chmod(file, st.st_mode | stat.S_IEXEC)

def ensure_rustup_target_installed(target_triple):
  rustup_exe = shutil.which('rustup')
  if rustup_exe is None:
    raise Exception(f'Cannot test to see if environment {target_triple} is installed because rustup is not available!')
  targets_out = subprocess.run([
    rustup_exe, 'target', 'list'
  ], capture_output=True, text=True).stdout

  for line in targets_out.splitlines():
    if target_triple in line and 'installed' in line:
      return

  print(f'> Installing rust target {target_triple}')
  subprocess.run([
    rustup_exe, 'target', 'add', target_triple
  ], check=True)

def find_dir_file_resides_in(directory, file, max_recursion=3):
  if max_recursion < 1:
    return None

  for filename in os.listdir(directory):
    full_filename = os.path.join(directory, filename)
    if filename == file:
      return directory
    if os.path.isdir(full_filename):
      maybe_found_file = find_dir_file_resides_in(full_filename, file, max_recursion=max_recursion-1)
      if maybe_found_file is not None:
        return maybe_found_file

  return None

def setup_cargo_cc_ar_tools(target_triple, linker_program, ar_program):
  if not os.path.exists('.cargo'):
    os.makedirs('.cargo')
  with open(os.path.join('.cargo', 'config.toml'), 'w') as fd:

    fd.write(f'[target.{target_triple}]\n')
    
    if linker_program is not None and os.path.exists(linker_program):
      fd.write(f'linker = "{linker_program}"\n')

    if ar_program is not None and os.path.exists(ar_program):
      fd.write(f'ar = "{ar_program}"\n')

    fd.write('\n')

def get_first_installed_bin(*bins):
  for b in bins:
    if b is None:
      continue
    b_path = shutil.which(b)
    if b_path is not None:
      return b_path
  return None

def gen_all_apple_darwin_bins_between(begin_version, end_version, format_s):
  return [
    format_s.format( version=round(float(version) / 10.0, 1), v=round(float(version) / 10.0, 1) ) for version in range(int(begin_version * 10.0), int(end_version * 10.0), 1)
  ]

def cargo_build_target(project_name, target_triple):
  print(f'> building {project_name} for {target_triple}...')
  ensure_rustup_target_installed(target_triple)

  # first attempt target built using zig
  use_zig = not ENV_D.get('nozig', False)
  if use_zig:
    # Attempt to use zig
    zig_host_exe = shutil.which('zig')
    if zig_host_exe is None:
      ENV_D['nozig'] = True
    else:
      zig_adapters_dir = os.path.join('btool', 'zig-adapters', target_triple)
      if not os.path.exists(zig_adapters_dir):
        os.makedirs(zig_adapters_dir)

      zig_cc_script = os.path.join(zig_adapters_dir, 'cc')
      zig_ar_script = os.path.join(zig_adapters_dir, 'ar')
      if not os.path.exists(zig_cc_script) or not os.path.exists(zig_ar_script):
        if not os.path.exists(zig_cc_script):
          with open(zig_cc_script, 'w') as fd:
            fd.write(f'''
#!/bin/sh
exec zig cc -target {target_triple} $@
'''.strip())
          make_f_executable(zig_cc_script)

        if not os.path.exists(zig_ar_script):
          with open(zig_ar_script, 'w') as fd:
            fd.write(f'''
#!/bin/sh
exec zig ar -target {target_triple} $@
'''.strip())
          make_f_executable(zig_ar_script)

        raise Exception(f'Please fill in the zig CC script templates {zig_adapters_dir} for the target triple {target_triple}')

      else:
        # adapters exist, ammend .cargo/config.toml to use the adapters for the triple
        setup_cargo_cc_ar_tools(target_triple, os.path.abspath(zig_cc_script), os.path.abspath(zig_ar_script))

  else:

    # Do not use zig, test for existence of mingw / osxcross and write those to .cargo/config.toml
    cc_program = get_first_installed_bin(
      'x86_64-w64-mingw32-cc' if 'windows' in target_triple else None,
      *(gen_all_apple_darwin_bins_between(19.0, 22.0, 'x86_64-apple-darwin{version}-clang') if 'darwin' in target_triple else [None]),
      'gcc', 'clang',
    )
    ar_program = get_first_installed_bin(
      'x86_64-w64-mingw32-ar' if 'windows' in target_triple else None,
      *(gen_all_apple_darwin_bins_between(19.0, 22.0, 'x86_64-apple-darwin{version}-ar') if 'darwin' in target_triple else [None]),
      'ar'
    )
    if 'windows' in target_triple and (not os.name == 'nt') and not ('mingw32' in cc_program and 'mingw32' in ar_program):
      print(f'WARNING> detected cross-compile (target_triple={target_triple}) but no mingw32 binaries found!')

    if 'darwin' in target_triple and (not 'darwin' in sys.platform) and not ('darwin' in cc_program and 'darwin' in ar_program):
      print(f'WARNING> detected cross-compile (target_triple={target_triple}) but no darwin-specific binaries found!')

    print(f'cc_program={cc_program}')
    print(f'ar_program={ar_program}')

    setup_cargo_cc_ar_tools(target_triple, cc_program, ar_program)


  cargo_env = {}
  cargo_env.update(os.environ)
  
  run_cmd = [
    'cargo', 'build', '-p', project_name, '--release', '--target', target_triple
  ]

  print(f'> {" ".join(run_cmd)}')

  subprocess.run(run_cmd, env=cargo_env, check=True)

  print(f'> Built {project_name} for {target_triple}!')





def build_desktop_x86_64_pc_windows_gnu():
  cargo_build_target('infostream-desktop', 'x86_64-pc-windows-gnu')

def build_desktop_x86_64_unknown_linux_gnu():
  cargo_build_target('infostream-desktop', 'x86_64-unknown-linux-gnu')

def build_desktop_x86_64_apple_darwin():
  cargo_build_target('infostream-desktop', 'x86_64-apple-darwin')





