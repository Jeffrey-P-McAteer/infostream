
import os
import stat
import sys
import subprocess
import shutil

def main(args=sys.argv):
  move_to_repo_root()

  #build_desktop_x86_64_unknown_linux_gnu()
  build_desktop_x86_64_pc_windows_gnu()
  #build_desktop_x86_64_apple_darwin()
  

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

def get_addtl_link_args(target_triple):
  args = []

  if 'windows' in target_triple:
    # libs_we_need = [
    #   'libgcc_eh.a', 'libpthread.a'
    # ]
    # if os.path.exists(os.environ.get('BTOOL_USR_MINGW32_DIR', '/usr/x86_64-w64-mingw32')):
    #   for lib_name in libs_we_need:
    #     lib_folder = find_dir_file_resides_in('/usr/x86_64-w64-mingw32', lib_name)
    #     if lib_folder is not None:
    #       args.append('-L{}'.format(lib_folder))

    # if os.path.exists(os.environ.get('BTOOL_USR_LIB_GCC_MINGW32_DIR', '/usr/lib/gcc/x86_64-w64-mingw32')):
    #   for lib_name in libs_we_need:
    #     lib_folder = find_dir_file_resides_in('/usr/lib/gcc/x86_64-w64-mingw32', lib_name)
    #     if lib_folder is not None:
    #       args.append('-L{}'.format(lib_folder))
    pass



  elif 'macos' in target_triple:
    # if os.path.exists('/opt/osxcross/target/SDK/MacOSX11.3.sdk/usr/lib'):
    #   args.append('-L/opt/osxcross/target/SDK/MacOSX11.3.sdk/usr/lib')
    # if os.path.exists('/opt/osxcross/target/lib'):
    #   args.append('-L/opt/osxcross/target/lib')
    pass

  return args

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
exec zig cc -target {target_triple} "${{ZIG_ADDTL_LINK_ARGS[@]}}" $@
'''.strip())
      make_f_executable(zig_cc_script)

    if not os.path.exists(zig_ar_script):
      with open(zig_ar_script, 'w') as fd:
        fd.write(f'''
#!/bin/sh
exec zig ar -target {target_triple} "${{ZIG_ADDTL_LINK_ARGS[@]}}" $@
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
  # cargo_env['CC'] = os.path.abspath(zig_cc_script)
  cargo_env['ZIG_ADDTL_LINK_ARGS'] = ' '.join(get_addtl_link_args(target_triple))

  run_cmd = [
    'cargo', 'build', '-p', project_name, '--release', '--target', target_triple
  ]

  # print(f'> CC={cargo_env["CC"]}')
  print(f'> ZIG_ADDTL_LINK_ARGS={cargo_env["ZIG_ADDTL_LINK_ARGS"]}')
  print(f'> {" ".join(run_cmd)}')

  subprocess.run(run_cmd, env=cargo_env, check=True)

  print(f'> Built {project_name} for {target_triple}!')





def build_desktop_x86_64_pc_windows_gnu():
  cargo_build_target('infostream-desktop', 'x86_64-pc-windows-gnu')

def build_desktop_x86_64_unknown_linux_gnu():
  cargo_build_target('infostream-desktop', 'x86_64-unknown-linux-gnu')

def build_desktop_x86_64_apple_darwin():
  cargo_build_target('infostream-desktop', 'x86_64-apple-darwin')





