# YGO Duel Clone (Custom Engine)

Este projeto é uma implementação de mecânicas de duelo de Yu-Gi-Oh! construída sobre uma **engine propia 2D** desenvolvida em Python.

A engine utiliza **Cython** para otimização de performance em áreas críticas como rasterização de software, cálculos geométricos e matemática vetorial. Por este motivo, o processo de instalação requer etapas de compilação de código C.

## 📋 Pré-requisitos

Antes de iniciar, certifique-se de que seu ambiente de desenvolvimento possui as seguintes ferramentas:

1. **Python 3.11**
2. **UV (Package Manager):** Foi utilizado `uv` para gerenciament de dependências.
* [Instalar UV](https://github.com/astral-sh/uv)


3. **Compilador C++ (Crítico para Cython):**
* **Windows:** É **obrigatório** ter o **Microsoft Visual C++ Build Tools** instalado.
* Baixe o *Visual Studio Installer*.
* Selecione a carga de trabalho "Desenvolvimento para desktop com C++".


* **Linux/MacOS:** `gcc`, `build-essential` e `python3-dev`.



> ⚠️ **Aviso:** Sem um compilador C++ configurado no PATH, o comando de build da engine (`setup.py`) falhará ao tentar compilar os arquivos `.pyx`.

## 🚀 Instalação e Build

Siga os passos abaixo para configurar o ambiente e compilar a engine.

### 1. Configurar o Ambiente Virtual (com UV)

```bash
# Clone o repositório
git clone <seu-repo-url>
cd <seu-repo-dir>

# Crie o ambiente virtual
uv venv

# Ative o ambiente
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instale as dependências (incluindo Cython e Pygame)
uv sync

```

### 2. Compilar a Engine (Cython Build)

A engine possui módulos de alta performance (rasterização, matemática, colisão) escritos em Cython (`.pyx`) que precisam ser compilados em código de máquina nativo (`.pyd` ou `.so`).

Execute o seguinte comando na raiz do projeto:

```bash
python setup.py build_ext --inplace --force

```

* `build_ext`: Comando para construir extensões C/C++.
* `--inplace`: Gera os arquivos compilados diretamente na árvore de diretórios do código fonte (necessário para importar como módulos Python normais).
* `--force`: Força a recompilação mesmo se os arquivos parecerem atualizados (garante que alterações no `.pxd`/`.pyx` sejam aplicadas).

## 📂 Estrutura do Projeto

O projeto segue uma arquitetura separada entre a tecnologia base (Engine) e a lógica de jogo (Game).

```text
.
├── engine/                 # Core Framework (Reutilizável)
│   ├── core/               # Gerenciamento de Recursos, Tipos base
│   ├── graphics/           # Pipeline de Renderização (Cythonizado)
│   │   └── rasterizer/     # Primitivas gráficas (Line, Rect, Polygon) em C
│   ├── math/               # Biblioteca Matemática (Vectors, Affine) em C
│   ├── ui/                 # Sistema de UI (Containers, Widgets, Layouts)
│   └── scene/              # Grafo de Cena (Scene Tree, Nodes, Signals)
│
├── game/                   # Implementação do YGO (Gameplay)
│   ├── entities/           # Objetos de Jogo (Card, Slot, Board, Deck)
│   ├── mechanics/          # Regras, Cadeia de Efeitos e Estados
│   ├── scenes/             # Cenas específicas (DuelScene, MainMenu)
│   └── content/            # Dados das cartas e scripts
│
├── assets/                 # Texturas, Fontes e Paletas
├── main.py                 # Ponto de entrada da aplicação
└── setup.py                # Script de build para módulos Cython

```

## ▶️ Como Rodar

Após a compilação bem-sucedida, execute o jogo através do ponto de entrada principal:

```bash
python main.py

```