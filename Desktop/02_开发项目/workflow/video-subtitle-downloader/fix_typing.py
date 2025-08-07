import os
import re

def fix_typing_imports(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否使用了 Any 但没有导入
                if 'Any' in content and 'from typing import' in content:
                    # 修复导入行
                    content = re.sub(
                        r'from typing import ([^,\n]*?)(?=\n|$)',
                        lambda m: f'from typing import {m.group(1)}, Any' if 'Any' not in m.group(1) else m.group(0),
                        content
                    )
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f'修复了: {filepath}')

fix_typing_imports('universal_subtitle_downloader')
print('✅ 所有 typing 导入问题已修复')
