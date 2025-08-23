from flask import Flask, render_template, request, jsonify
import subprocess
import os
import re

app = Flask(__name__)

# Sanitize user-submitted code
def sanitize_code(code):
    dangerous_patterns = [
        r'\bsystem\s*\(', r'\bexec\s*\(', r'\bpopen\s*\(', r'\bfork\s*\(',
        r'\bexecl\s*\(', r'\bexeclp\s*\(', r'\bexecle\s*\(', r'\bexecv\s*\(',
        r'\bexecvp\s*\(', r'\bexecve\s*\(', r'\bopen\s*\(', r'\bunlink\s*\(',
        r'\bremove\s*\(', r'\brename\s*\(', r'\bchmod\s*\(', r'\bchown\s*\(',
        r'\blink\s*\(', r'\bsymlink\s*\(', r'\bifstream\s+', r'\bofstream\s+',
        r'\bfopen\s*\(',
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, code, flags=re.IGNORECASE):
            return "⚠️⚠️⚠️ Dangerous function detected."
    return code

# Root route to serve the frontend
@app.route('/')
def index():
    return render_template('index.html')

# Endpoint to compile and execute C++ code
@app.route('/compile', methods=['POST'])
def compile_code():
    data = request.get_json()
    code = data.get('code')

    # Sanitize the code
    sanitized_code = sanitize_code(code)
    if sanitized_code == "⚠️⚠️⚠️ Dangerous function detected.":
        return jsonify({"output": "⚠️⚠️⚠️ Dangerous function detected."})

    temp_file = "/app/tmp/temp.cpp"
    output_file = "/app/tmp/output"
    try:
        # Write sanitized code to a temporary file
        with open(temp_file, "w") as f:
            f.write(sanitized_code)

        # Compile the code
        compile_result = subprocess.run(
            ["g++", temp_file, "-o", output_file],
            capture_output=True, text=True, timeout=5
        )
        if compile_result.returncode != 0:
            return jsonify({"output": f"Compilation Error:\n{compile_result.stderr}"})

        # Run the compiled program
        run_result = subprocess.run(
            [output_file], capture_output=True, text=True, timeout=5
        )
        return jsonify({
            "output": run_result.stdout or run_result.stderr or "No output."
        })

    except subprocess.TimeoutExpired:
        return jsonify({"output": "Error: Execution timed out."})
    except Exception as e:
        return jsonify({"output": f"An unexpected error occurred: {str(e)}"})
    finally:
        # Clean up temporary files
        if os.path.exists(temp_file):
            os.remove(temp_file)
        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)