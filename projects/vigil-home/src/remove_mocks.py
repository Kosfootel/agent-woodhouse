import re
import sys

files_to_patch = [
    '/home/erik-ross/vigil/dashboard/src/components/AccessHeatmap.js',
    '/home/erik-ross/vigil/dashboard/src/components/AlertPanel.js',
    '/home/erik-ross/vigil/dashboard/src/components/EventTimeline.js',
    '/home/erik-ross/vigil/dashboard/src/components/ToolChart.js',
]

for filepath in files_to_patch:
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Pattern to find mock data blocks
        # Look for: const mockData = {...}; or similar
        # And the try/catch that uses it
        
        # Replace mock data fallbacks with empty data
        content = re.sub(
            r'const\s+mock\w*\s*=\s*\{[^}]+\};',
            '',
            content,
            flags=re.DOTALL
        )
        
        # Replace the try/catch mock fallback pattern
        content = re.sub(
            r'try\s*\{\s*const\s+response\s*=\s*await\s+\w+\([^)]*\)\;?\s*set\w+\(response[^)]+\)\;?\s*\}\s*catch\s*\([^)]+\)\s*\{[^}]*console\.log\s*\(\s*["\']Using\s+mock[^"\']*["\'][^}]*\}\s*set\w+\(mock\w*\)\;?',
            r'try {\n      const response = await \1\n      setData(response.data || []);\n    } catch (err) {\n      console.error("Failed to fetch data:", err);\n      setData([]);\n    }',
            content
        )
        
        # Remove mockData references in catch blocks
        content = re.sub(
            r'catch\s*\([^)]+\)\s*\{[^}]*console\.log\s*\(\s*["\']Using\s+mock[^"\']*["\'][^}]*\}\s*',
            'catch (err) {\n      console.error("Failed to fetch data:", err);\n    }\n    ',
            content
        )
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f'Patched {filepath}')
    except Exception as e:
        print(f'Error patching {filepath}: {e}')

print('Done removing mock data')
