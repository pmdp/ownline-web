from ownline_web import app
import subprocess


def execute_command(cmd):
    app.logger.debug("Executing command: {}".format(" ".join(cmd)))
    if app.env == 'production':
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        app.logger.debug("Execution result: code: {}, stderr: {}, stdout: {}".format(result.returncode,
                                                                                 result.stderr.decode(),
                                                                                 result.stdout.decode()))
        if result.returncode == 0:
            return True, result.stderr.decode(), result.stdout.decode()
        else:
            return False, result.stderr.decode(), result.stdout.decode()
    else:
        return True, 'stderr', 'stdout'
