# CFG Parser — Derivation Tree & AST Generator

Proyecto de la materia **ST0244 - Programming Languages and Computing Paradigms**
Universidad EAFIT

---

## 📌 Descripción

Este proyecto implementa un **parser para gramáticas libres de contexto (CFG)** utilizando el **algoritmo de Earley**, permitiendo:

* Validar gramáticas en formato BNF
* Generar derivaciones (izquierda y derecha)
* Visualizar el árbol de derivación
* Construir el Abstract Syntax Tree (AST)
* Interactuar mediante una interfaz gráfica (GUI)

---

## ⚙️ Tecnologías usadas

* Python 3
* Tkinter (GUI)
* Matplotlib (visualización)
* Pillow (manejo de imágenes)

---

## 🚀 Cómo ejecutar el proyecto

### 1. Clonar el repositorio

```bash
git clone https://github.com/chalo2322/practica-2.git
cd practica-2
```

### 2. Crear entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install matplotlib Pillow
```

### 4. Ejecutar la aplicación

```bash
python main.py
```

---

## 🧪 Ejemplo de uso

### Gramática:

```
E -> E + T | T
T -> T * F | F
F -> num
```

### Expresión:

```
num + num * num
```

---

## 🧠 Conceptos clave

* Gramáticas libres de contexto (CFG)
* Derivación izquierda y derecha
* Árbol de derivación
* Abstract Syntax Tree (AST)
* Algoritmo de Earley

---

## 📂 Estructura del proyecto

* `main.py` → Interfaz gráfica
* `grammar.py` → Lógica del parser y derivación
* `tree_visualizer.py` → Visualización de árboles

---

## 👨‍💻 Autor

Juan Gonzalo Echavarría
Salome Naomi Garcia Tabares
---

