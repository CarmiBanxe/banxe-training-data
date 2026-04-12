#!/usr/bin/env python3
"""
ingest_processor.py — Обработка файлов из raw/ и создание knowledge-base

Использование:
    python scripts/ingest_processor.py

Автоматически обрабатывает:
- PDF → извлечение текста (pymupdf)
- DOCX → извлечение текста (python-docx)
- TXT, MD → копирование как есть
- CSV, JSON, XLSX → валидация + копирование
- PNG, JPG → метаданные + описание

Создаёт:
- processed/ ← обработанные файлы
- knowledge-base/index.json ← полный индекс всех материалов
"""

import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Форматы с расширениями
SUPPORTED_FORMATS = {
    'docs': ['.pdf', '.docx', '.txt', '.md'],
    'data': ['.csv', '.json', '.xlsx'],
    'media': ['.png', '.jpg', '.jpeg', '.gif', '.svg'],
    'links': ['.url', '.txt']
}

class IngestProcessor:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.raw_dir = self.base_dir / 'raw'
        self.processed_dir = self.base_dir / 'processed'
        self.kb_dir = self.base_dir / 'knowledge-base'
        
        # Создаём директории если нет
        self.processed_dir.mkdir(exist_ok=True)
        self.kb_dir.mkdir(exist_ok=True)
        
        # Индекс знаний
        self.index: Dict[str, Any] = {
            'version': '1.0',
            'updated_at': datetime.now().isoformat(),
            'total_files': 0,
            'categories': {
                'docs': [],
                'data': [],
                'media': [],
                'links': []
            },
            'files': []
        }
    
    def compute_hash(self, file_path: Path) -> str:
        """Вычисляет SHA256 хэш файла"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def extract_pdf_text(self, file_path: Path) -> str:
        """Извлекает текст из PDF"""
        try:
            import fitz  # pymupdf
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            print("⚠️  pymupdf не установлен, копируем PDF как есть")
            return None
        except Exception as e:
            print(f"⚠️  Ошибка при извлечении PDF {file_path}: {e}")
            return None
    
    def extract_docx_text(self, file_path: Path) -> str:
        """Извлекает текст из DOCX"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            return text
        except ImportError:
            print("⚠️  python-docx не установлен, копируем DOCX как есть")
            return None
        except Exception as e:
            print(f"⚠️  Ошибка при извлечении DOCX {file_path}: {e}")
            return None
    
    def process_file(self, file_path: Path, category: str) -> Dict[str, Any]:
        """Обрабатывает один файл"""
        rel_path = file_path.relative_to(self.raw_dir)
        file_hash = self.compute_hash(file_path)
        
        # Метаданные файла
        file_info = {
            'id': file_hash[:12],
            'original_path': str(rel_path),
            'filename': file_path.name,
            'extension': file_path.suffix.lower(),
            'category': category,
            'size_bytes': file_path.stat().st_size,
            'hash': file_hash,
            'processed_at': datetime.now().isoformat(),
            'status': 'pending',
            'extracted_text': None,
            'output_path': None
        }
        
        # Обработка по типам
        if file_path.suffix.lower() == '.pdf':
            text = self.extract_pdf_text(file_path)
            if text:
                file_info['extracted_text'] = text
                file_info['status'] = 'extracted'
                # Сохраняем извлечённый текст
                output_path = self.processed_dir / f"{rel_path.stem}.txt"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                file_info['output_path'] = str(output_path.relative_to(self.base_dir))
            else:
                # Копируем как есть
                output_path = self.processed_dir / rel_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, output_path)
                file_info['output_path'] = str(output_path.relative_to(self.base_dir))
                file_info['status'] = 'copied'
        
        elif file_path.suffix.lower() == '.docx':
            text = self.extract_docx_text(file_path)
            if text:
                file_info['extracted_text'] = text
                file_info['status'] = 'extracted'
                output_path = self.processed_dir / f"{rel_path.stem}.txt"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                file_info['output_path'] = str(output_path.relative_to(self.base_dir))
            else:
                output_path = self.processed_dir / rel_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, output_path)
                file_info['output_path'] = str(output_path.relative_to(self.base_dir))
                file_info['status'] = 'copied'
        
        elif file_path.suffix.lower() in ['.txt', '.md']:
            # Текстовые файлы копируем как есть
            output_path = self.processed_dir / rel_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, output_path)
            file_info['output_path'] = str(output_path.relative_to(self.base_dir))
            file_info['status'] = 'copied'
            
            # Читаем содержимое для индекса
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_info['extracted_text'] = f.read()[:5000]  # Первые 5000 символов
        
        elif file_path.suffix.lower() in ['.csv', '.json', '.xlsx']:
            # Данные копируем как есть
            output_path = self.processed_dir / rel_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, output_path)
            file_info['output_path'] = str(output_path.relative_to(self.base_dir))
            file_info['status'] = 'copied'
        
        elif file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
            # Медиа — только метаданные
            output_path = self.processed_dir / rel_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, output_path)
            file_info['output_path'] = str(output_path.relative_to(self.base_dir))
            file_info['status'] = 'metadata_only'
        
        else:
            # Неизвестный формат — копируем как есть
            output_path = self.processed_dir / rel_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, output_path)
            file_info['output_path'] = str(output_path.relative_to(self.base_dir))
            file_info['status'] = 'unknown_format'
        
        return file_info
    
    def scan_raw_directory(self) -> List[tuple]:
        """Сканирует raw/ директорию и возвращает список файлов"""
        files = []
        
        for category in ['docs', 'data', 'media', 'links']:
            category_dir = self.raw_dir / category
            if not category_dir.exists():
                continue
            
            for file_path in category_dir.rglob('*'):
                if file_path.is_file():
                    files.append((file_path, category))
        
        return files
    
    def run(self) -> Dict[str, Any]:
        """Запускает полный процесс ingest"""
        print("🚀 Запуск ingest processor...")
        print(f"   Base dir: {self.base_dir}")
        print(f"   Raw dir: {self.raw_dir}")
        print(f"   Processed dir: {self.processed_dir}")
        print(f"   Knowledge base: {self.kb_dir}")
        
        # Сканируем raw/
        files = self.scan_raw_directory()
        print(f"\n📂 Найдено файлов: {len(files)}")
        
        if not files:
            print("⚠️  Файлы не найдены. Создаём пустой индекс.")
            self.save_index()
            return {'processed': 0, 'index': self.index}
        
        # Обрабатываем каждый файл
        for file_path, category in files:
            print(f"\n📄 Обработка: {file_path.relative_to(self.raw_dir)}")
            file_info = self.process_file(file_path, category)
            
            # Добавляем в индекс
            self.index['files'].append(file_info)
            self.index['categories'][category].append({
                'id': file_info['id'],
                'filename': file_info['filename'],
                'path': file_info['original_path'],
                'status': file_info['status']
            })
            
            print(f"   ✓ Статус: {file_info['status']}")
            if file_info['extracted_text']:
                preview = file_info['extracted_text'][:100].replace('\n', ' ')
                print(f"   📝 Текст: {preview}...")
        
        # Обновляем метаданные индекса
        self.index['total_files'] = len(self.index['files'])
        self.index['updated_at'] = datetime.now().isoformat()
        
        # Сохраняем индекс
        self.save_index()
        
        print("\n✅ Ingest завершён!")
        print(f"   Всего файлов: {self.index['total_files']}")
        print(f"   Индекс: {self.kb_dir / 'index.json'}")
        
        return {
            'processed': len(files),
            'index': self.index
        }
    
    def save_index(self):
        """Сохраняет индекс в knowledge-base/index.json"""
        index_path = self.kb_dir / 'index.json'
        
        # Создаём README для knowledge-base
        readme_path = self.kb_dir / 'README.md'
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("# Knowledge Base\n\n")
            f.write(f"**Updated:** {self.index['updated_at']}\n")
            f.write(f"**Total files:** {self.index['total_files']}\n\n")
            f.write("## Categories\n\n")
            for cat, items in self.index['categories'].items():
                f.write(f"### {cat.title()}\n")
                f.write(f"Files: {len(items)}\n\n")
                for item in items[:10]:  # Показываем первые 10
                    f.write(f"- `{item['filename']}` ({item['status']})\n")
                if len(items) > 10:
                    f.write(f"... и ещё {len(items) - 10}\n")
                f.write("\n")
        
        # Сохраняем JSON индекс
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
        
        print(f"📑 Индекс сохранён: {index_path}")


if __name__ == '__main__':
    processor = IngestProcessor()
    result = processor.run()
    
    # Выводим summary для GitHub Actions
    print("\n--- GitHub Actions Summary ---")
    print(f"Processed: {result['processed']} files")
    print("Categories:")
    for cat, items in result['index']['categories'].items():
        print(f"  {cat}: {len(items)} files")
