#!/bin/bash
# Migrate test files from Node test runner to Vitest

for file in frontend/src/**/*.test.{ts,tsx}; do
  if [ -f "$file" ]; then
    echo "Migrating $file..."

    # Replace node:assert with vitest expect
    sed -i.bak 's/import assert from .node:assert\/strict./import { expect } from '\''vitest'\''/' "$file"
    sed -i.bak 's/from .node:assert\/strict./from '\''vitest'\''/' "$file"

    # Replace node:test imports with vitest imports
    sed -i.bak 's/import { \(.*\) } from .node:test./import { \1 } from '\''vitest'\''/' "$file"
    sed -i.bak 's/from .node:test./from '\''vitest'\''/' "$file"

    # Replace assert.equal with expect().toBe()
    sed -i.bak 's/assert\.equal(\([^,]*\), \([^)]*\))/expect(\1).toBe(\2)/' "$file"

    # Replace assert.deepEqual with expect().toEqual()
    sed -i.bak 's/assert\.deepEqual(\([^,]*\), \([^)]*\))/expect(\1).toEqual(\2)/' "$file"

    # Replace assert.ok with expect().toBeTruthy()
    sed -i.bak 's/assert\.ok(\([^)]*\))/expect(\1).toBeTruthy()/' "$file"

    # Replace assert.throws with expect().toThrow()
    sed -i.bak 's/assert\.throws(\([^)]*\))/expect(\1).toThrow()/' "$file"

    # Remove backup files
    rm -f "$file.bak"
  fi
done

echo "Migration complete!"
