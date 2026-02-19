
import os
import sys
import subprocess
import json
import re

# Structured Error Output
RESULTS = {
    "status": "FAILED",
    "language": "Unknown",
    "exit_code": 1,
    "errors": [],
    "raw_logs": ""
}

LANGUAGE_CONFIG = {
    "python": {
        "files": ["requirements.txt", "Pipfile", "pyproject.toml", "setup.py", "*.py"],
        "install": ["pip install -r requirements.txt"] if os.path.exists("requirements.txt") else [],
        "test": ["pytest"], # Fallback?
        "error_pattern": r'File "(.+?)", line (\d+)'
    },
    "node": {
        "files": ["package.json", "*.js", "*.ts"],
        "install": ["npm install"],
        "test": ["npm test"],
        "error_pattern": r'at (.+?):(\d+):(\d+)'
    },
    "java_maven": {
        "files": ["pom.xml"],
        "install": [],
        "test": ["mvn test"],
        "error_pattern": r'(.+?):\[(\d+),(\d+)\]' 
    },
    "java_gradle": {
        "files": ["build.gradle"],
        "install": [],
        "test": ["gradle test"],
        "error_pattern": r'(.+?):(\d+): error' 
    },
    "go": {
        "files": ["go.mod", "*.go"],
        "install": [],
        "test": ["go test ./..."],
        "error_pattern": r'(.+?):(\d+):'
    },
    "csharp": {
        "files": ["*.csproj", "*.sln"],
        "install": [],
        "test": ["dotnet test"],
        "error_pattern": r'(.+?)\((\d+),(\d+)\): error'
    },
    "cpp": {
        "files": ["Makefile", "CMakeLists.txt", "*.cpp", "*.c"],
        "install": [],
        "test": ["make"], # Highly variable
        "error_pattern": r'(.+?):(\d+):(\d+): error'
    },
    "rust": {
        "files": ["Cargo.toml", "*.rs"],
        "install": [],
        "test": ["cargo test"],
        "error_pattern": r'--> (.+?):(\d+):(\d+)'
    },
    "php": {
        "files": ["composer.json", "*.php"],
        "install": ["composer install"],
        "test": ["vendor/bin/phpunit"],
        "error_pattern": r'on line (\d+) in (.+?)'
    },
    "ruby": {
        "files": ["Gemfile", "*.rb"],
        "install": ["bundle install"],
        "test": ["rspec"],
        "error_pattern": r'(.+?):(\d+):in'
    }
}

def detect_language():
    # Priority check
    if os.path.exists("pom.xml"): return "java_maven"
    if os.path.exists("build.gradle"): return "java_gradle"
    if os.path.exists("package.json"): return "node"
    if os.path.exists("go.mod"): return "go"
    if os.path.exists("Cargo.toml"): return "rust"
    if os.path.exists("requirements.txt"): return "python"
    
    # Fallback to extension scan
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".csproj"): return "csharp"
            if file.endswith(".sln"): return "csharp"
            if file.endswith(".py"): return "python"
            if file.endswith(".js"): return "node"
            if file.endswith(".ts"): return "node"
            if file.endswith(".go"): return "go"
            if file.endswith(".java"): return "java_maven" # Default to maven?
            if file.endswith(".cpp") or file.endswith(".c"): return "cpp"
            if file.endswith(".rs"): return "rust"
            if file.endswith(".php"): return "php"
            if file.endswith(".rb"): return "ruby"
    
    return "unknown"

def run_command(cmd):
    try:
        # Capture strictly
        result = subprocess.run(
            cmd, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def extract_errors(logs, language):
    errors = []
    config = LANGUAGE_CONFIG.get(language, {})
    pattern = config.get("error_pattern")
    
    if not pattern:
        return []
        
    matches = re.findall(pattern, logs)
    # Normailize
    for m in matches:
        err = {"file": "", "line": 0, "message": "Detected Error"}
        
        # Heuristics for groups
        # Python: (file, line)
        # Node: (file, line, col)
        if language == "python":
            err["file"] = m[0]
            err["line"] = int(m[1])
        elif language == "node":
            err["file"] = m[0]
            err["line"] = int(m[1])
        # Add more mappings as needed
        
        errors.append(err)
        
    return errors

def main():
    try:
        lang = detect_language()
        RESULTS["language"] = lang
        
        if lang == "unknown":
            print(json.dumps(RESULTS))
            return

        config = LANGUAGE_CONFIG.get(lang, {})
        
        # Install
        for cmd in config.get("install", []):
            code, out, err = run_command(cmd)
            RESULTS["raw_logs"] += f"\n[INSTALL] {cmd}\n{out}\n{err}\n"
            if code != 0:
                RESULTS["status"] = "INSTALL_FAILED"
                RESULTS["exit_code"] = code
                print(json.dumps(RESULTS))
                return

        # Test
        test_cmds = config.get("test", [])
        if not test_cmds:
             RESULTS["raw_logs"] += "\nNo test command configured.\n"
             print(json.dumps(RESULTS))
             return

        # Just verify we have files first for Python logs if needed
        # Run test
        final_code = 0
        for cmd in test_cmds:
            code, out, err = run_command(cmd)
            RESULTS["raw_logs"] += f"\n[TEST] {cmd}\n{out}\n{err}\n"
            if code != 0:
                final_code = code

        RESULTS["exit_code"] = final_code
        RESULTS["status"] = "PASSED" if final_code == 0 else "FAILED"
        
        if final_code != 0:
            RESULTS["errors"] = extract_errors(RESULTS["raw_logs"], lang)

        print(json.dumps(RESULTS))
        
    except Exception as e:
        RESULTS["status"] = "SYSTEM_ERROR"
        RESULTS["raw_logs"] += str(e)
        print(json.dumps(RESULTS))

if __name__ == "__main__":
    main()
