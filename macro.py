import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Union

from pynput import mouse, keyboard

# =========================
# Helpers de serialização
# =========================

def serialize_key(key: Union[keyboard.Key, keyboard.KeyCode]) -> Dict[str, Any]:
    if isinstance(key, keyboard.KeyCode):
        return {"type": "KeyCode", "char": key.char}
    else:
        return {"type": "Key", "name": key.name}

def deserialize_key(obj: Dict[str, Any]) -> Union[keyboard.Key, keyboard.KeyCode]:
    if obj["type"] == "KeyCode":
        # Pode ser None em algumas teclas de controle; escolha segura
        return keyboard.KeyCode.from_char(obj["char"]) if obj.get("char") else keyboard.Key.esc
    else:
        return getattr(keyboard.Key, obj["name"])

def serialize_button(btn: mouse.Button) -> str:
    return btn.name  # "left", "right", "middle"

def deserialize_button(name: str) -> mouse.Button:
    return getattr(mouse.Button, name)

# =========================
# Gravação
# =========================

def record_macro(outfile: Path) -> None:
    """
    Grava eventos (mouse + teclado) em JSONL com timestamps relativos (campo 't').
    Para com ESC usando atalho global (robusto no macOS).
    """
    start_ts = time.perf_counter()
    events: List[Dict[str, Any]] = []

    def now() -> float:
        return round(time.perf_counter() - start_ts, 6)

    # --- Coleta de mouse ---
    def on_move(x, y):
        events.append({"t": now(), "type": "move", "x": int(x), "y": int(y)})

    def on_click(x, y, button, pressed):
        events.append({
            "t": now(), "type": "click", "x": int(x), "y": int(y),
            "button": serialize_button(button),
            "pressed": bool(pressed)
        })

    def on_scroll(x, y, dx, dy):
        events.append({
            "t": now(), "type": "scroll", "x": int(x), "y": int(y),
            "dx": int(dx), "dy": int(dy)
        })

    # --- Coleta de teclado (não depende dele para parar) ---
    def on_press(key):
        events.append({"t": now(), "type": "key", "pressed": True, "key": serialize_key(key)})

    def on_release(key):
        events.append({"t": now(), "type": "key", "pressed": False, "key": serialize_key(key)})

    stop_flag = {"stop": False}
    def _stop():
        stop_flag["stop"] = True

    print("🎥 Gravando... (aperte ESC para parar)")

    # Listeners principais
    ml = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    kl = keyboard.Listener(on_press=on_press, on_release=on_release)

    # Hotkey global para ESC
    hk = keyboard.GlobalHotKeys({'<esc>': _stop})

    try:
        ml.start()
        kl.start()
        hk.start()

        # Loop para permitir encerrar por hotkey sem bloquear a thread principal
        while not stop_flag["stop"]:
            time.sleep(0.01)
    finally:
        for l in (hk, kl, ml):
            try:
                l.stop()
            except Exception:
                pass

        # Persistir o que foi gravado
        outfile.parent.mkdir(parents=True, exist_ok=True)
        with outfile.open("w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")

        print(f"✅ Gravado {len(events)} eventos em {outfile}")

# =========================
# Reprodução
# =========================

def play_macro(
    infile: Path,
    speed: float = 1.0,
    mouse_only: bool = False,
    keyboard_only: bool = False,
    loop: bool = False
) -> None:
    """
    Reproduz eventos gravados. 'speed' ajusta o timing (2.0 = 2x mais rápido).
    Se loop=True, repete até CTRL+C.
    """
    if not infile.exists():
        raise SystemExit(f"Arquivo não encontrado: {infile}")

    events: List[Dict[str, Any]] = []
    with infile.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))

    if not events:
        print("Arquivo vazio, nada para reproduzir.")
        return

    mctl = mouse.Controller()
    kctl = keyboard.Controller()

    print(f"▶️ Reproduzindo {len(events)} eventos (speed={speed}x, loop={loop}, mouse_only={mouse_only}, keyboard_only={keyboard_only})")

    try:
        while True:
            base = events[0]["t"]
            start = time.perf_counter()

            def wait_until(event_t: float):
                target = (event_t - base) / max(0.0001, speed)
                while True:
                    elapsed = time.perf_counter() - start
                    delay = target - elapsed
                    if delay <= 0:
                        break
                    time.sleep(min(0.01, delay))

            for ev in events:
                wait_until(ev["t"])
                etype = ev["type"]

                # Filtros
                if mouse_only and etype not in ("move", "click", "scroll"):
                    continue
                if keyboard_only and etype != "key":
                    continue

                if etype == "move":
                    mctl.position = (ev["x"], ev["y"])

                elif etype == "click":
                    mctl.position = (ev["x"], ev["y"])
                    btn = deserialize_button(ev["button"])
                    if ev["pressed"]:
                        mctl.press(btn)
                    else:
                        mctl.release(btn)

                elif etype == "scroll":
                    mctl.scroll(ev["dx"], ev["dy"])

                elif etype == "key":
                    kinfo = ev["key"]
                    pressed = ev["pressed"]
                    try:
                        # Se for caractere Unicode (KeyCode com 'char'), use type() no press
                        if kinfo.get("type") == "KeyCode" and kinfo.get("char"):
                            if pressed:
                                import unicodedata
                                ch = unicodedata.normalize("NFC", kinfo["char"])
                                kctl.type(ch)
                            # Ignora o release para KeyCode de caractere
                            continue

                        # Teclas especiais (shift, ctrl, cmd, esc, etc.)
                        keyobj = deserialize_key(kinfo)
                        if pressed:
                            kctl.press(keyobj)
                        else:
                            kctl.release(keyobj)

                    except Exception as e:
                        print(f"⚠️ Ignorando tecla inválida: {kinfo} ({e})")

            if not loop:
                break

            print("⏳ Aguardando 3 minutos antes da próxima repetição...")
            time.sleep(200)

    except KeyboardInterrupt:
        print("\n⏹️ Execução interrompida pelo usuário.")

# =========================
# CLI
# =========================

def main():
    parser = argparse.ArgumentParser(description="Gravar e reproduzir macro (mouse + teclado) em JSONL.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record", help="Gravar macro")
    r.add_argument("outfile", type=Path, help="Arquivo de saída (.jsonl)")

    p = sub.add_parser("play", help="Reproduzir macro")
    p.add_argument("infile", type=Path, help="Arquivo .jsonl gravado")
    p.add_argument("--speed", type=float, default=1.0, help="Fator de velocidade (ex.: 2.0 = 2x mais rápido)")
    p.add_argument("--mouse-only", action="store_true", help="Reproduz apenas eventos de mouse")
    p.add_argument("--keyboard-only", action="store_true", help="Reproduz apenas eventos de teclado")
    p.add_argument("--loop", action="store_true", help="Repetir indefinidamente até CTRL+C")

    args = parser.parse_args()

    if args.cmd == "record":
        record_macro(args.outfile)
    elif args.cmd == "play":
        play_macro(
            args.infile,
            speed=args.speed,
            mouse_only=args.mouse_only,
            keyboard_only=args.keyboard_only,
            loop=args.loop  # <- GARANTE que o valor da flag chega na função
        )

if __name__ == "__main__":
    main()
