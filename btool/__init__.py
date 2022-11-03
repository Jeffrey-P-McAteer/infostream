
import os
import stat
import sys
import subprocess
import shutil

def main(args=sys.argv):
  move_to_repo_root()

  build_desktop_x86_64_unknown_linux_gnu()
  build_desktop_x86_64_pc_windows_gnu()
  build_desktop_x86_64_apple_darwin()
  

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

def cargo_build_target(project_name, target_triple):
  zig_host_exe = shutil.which('zig')
  if zig_host_exe is None:
    raise Exception(f'Cannot build {project_name} for {target_triple} because zig is not available!')

  ensure_rustup_target_installed(target_triple)

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

    with open(os.path.join('.cargo', 'config.toml'), 'a') as fd:
      fd.write('\n')
      fd.write(f'''
[target.{target_triple}]
linker = "./{zig_cc_script}"
ar = "./{zig_ar_script}"
'''.strip())

    raise Exception(f'Please fill in the zig CC script templates {zig_adapters_dir} for the target triple {target_triple}')

  cargo_env = {}
  cargo_env.update(os.environ)
  cargo_env['CC'] = os.path.abspath(zig_cc_script)

  subprocess.run([
    'cargo', 'build', '-p', project_name, '--release', '--target', target_triple
  ], env=cargo_env, check=True)

  print(f'> Built {project_name} for {target_triple}!')





def build_desktop_x86_64_pc_windows_gnu():
  cargo_build_target('infostream-desktop', 'x86_64-pc-windows-gnu')

def build_desktop_x86_64_unknown_linux_gnu():
  cargo_build_target('infostream-desktop', 'x86_64-unknown-linux-gnu')

def build_desktop_x86_64_apple_darwin():
  cargo_build_target('infostream-desktop', 'x86_64-apple-darwin')





