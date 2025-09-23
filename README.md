# 🎥 Macro Recorder & Player em Python

Este projeto permite **gravar** movimentos do mouse e teclado em um arquivo e **reproduzir** depois, com a mesma sequência e tempo.  
Funciona no **macOS, Linux e Windows** (com algumas diferenças de permissões no macOS).

---

## 🚀 Instalação do zero (macOS)

```
python3 -m venv bot_python_games
cd bot_python_games
source bin/activate
pip install pynput
```

```
python macro.py record meus_eventos.jsonl
```
```
python macro.py play meus_eventos.jsonl --loop
```