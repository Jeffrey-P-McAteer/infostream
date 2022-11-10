

// See https://rust-lang.github.io/rfcs/1665-windows-subsystem.html
//#[cfg(windows)]
#![windows_subsystem = "console"]

// #[cfg(windows)]
#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn WinMain(__mingw_winmain_hInstance: isize, _idk: isize, __mingw_winmain_lpCmdLine: isize, __mingw_winmain_nShowCmd: isize) -> isize {
  println!("WAT: {}", infostream::test_01() );
  return 1;
}

fn main() {
    
    println!("Hello, world: {}", infostream::test_01() );

}



