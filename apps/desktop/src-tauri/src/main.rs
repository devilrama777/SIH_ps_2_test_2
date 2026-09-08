// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::{AppHandle, Manager};

struct SidecarState {
    child: Mutex<Option<Child>>,
}

fn spawn_python_sidecar() -> Option<Child> {
    let mut cmd = Command::new("python");
    cmd.args(["-m", "apps.processing.server"]);

    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x08000000;
        cmd.creation_flags(CREATE_NO_WINDOW);
    }

    match cmd.spawn() {
        Ok(child) => {
            println!("Spawned Python backend sidecar with PID: {}", child.id());
            Some(child)
        }
        Err(e) => {
            eprintln!("Warning: Failed to launch python sidecar automatically: {}. Falling back to external daemon.", e);
            None
        }
    }
}

fn main() {
    tauri::Builder::default()
        .manage(SidecarState {
            child: Mutex::new(None),
        })
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let child = spawn_python_sidecar();
            let state = app.state::<SidecarState>();
            if let Ok(mut lock) = state.child.lock() {
                *lock = child;
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                let state = window.state::<SidecarState>();
                if let Ok(mut lock) = state.child.lock() {
                    if let Some(mut child) = lock.take() {
                        println!("Window destroyed. Terminating Python sidecar process...");
                        let _ = child.kill();
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running CIL Report AI desktop application");
}
