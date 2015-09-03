import subprocess

while True:
    proc = subprocess.Popen([r"C:\Program Files\Blender Foundation\Blender\blender.exe", r"C:\Users\Peter\Documents\Hills road\Computing\A2\COMP4\inaite\blender test files\reload.blend"],
                            shell=True,
                            stdout=subprocess.PIPE,
                            )
    while proc.poll() is None:
        output = proc.stdout.readline()
        print(output)
