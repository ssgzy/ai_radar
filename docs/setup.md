# 安装与运行

## 安装依赖

```bash
python -m pip install -r requirements.txt
```

## 检查 Ollama

```bash
python scripts/test_ollama.py
```

## 运行一次

```bash
python run_once.py --max-items 2
```

## 手动调试

```bash
python run_manual.py --sources arxiv github --max-items 2
```
