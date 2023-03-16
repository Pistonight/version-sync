# lint, need base-lint in the parent directory
lint FIX="":
    python ../base-lint . -c {{FIX}}
    pycodestyle .

