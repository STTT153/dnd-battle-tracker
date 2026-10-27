use std::sync::atomic::{AtomicBool, Ordering};
use tauri::{Emitter, Manager, RunEvent, State, WindowEvent};

#[derive(Default)]
struct CloseGuard(AtomicBool);

#[tauri::command]
fn session_set_close_guard(enabled: bool, guard: State<'_, CloseGuard>) {
    guard.0.store(enabled, Ordering::SeqCst);
}

#[tauri::command]
fn session_confirm_exit(app: tauri::AppHandle, guard: State<'_, CloseGuard>) {
    guard.0.store(false, Ordering::SeqCst);
    app.exit(0);
}

pub fn run() {
    let app = tauri::Builder::default()
        .manage(CloseGuard::default())
        .invoke_handler(tauri::generate_handler![session_set_close_guard, session_confirm_exit])
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                if window.state::<CloseGuard>().0.load(Ordering::SeqCst) {
                    api.prevent_close();
                    let _ = window.emit("session:request-exit", ());
                }
            }
        })
        .build(tauri::generate_context!())
        .expect("无法启动 Dungeon Master Studio");
    app.run(|handle, event| {
        // Normal macOS Quit can bypass the window's CloseRequested event.
        if let RunEvent::ExitRequested { code: None, api, .. } = event {
            if handle.state::<CloseGuard>().0.load(Ordering::SeqCst) {
                api.prevent_exit();
                if let Some(window) = handle.get_webview_window("main") {
                    let _ = window.emit("session:request-exit", ());
                }
            }
        }
    });
}
