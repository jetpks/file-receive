#!/usr/bin/env python
import os
import sys
import SocketServer
import tarfile
import uuid
import time
import re

# Some globals:
tmpDir          = './tmp/' # MUST END IN /
tmpFilePrefix   = 'recvr-'
targetDir       = '/tmp/mnt/sda1/tiles/' # ALSO MUST END IN /

class TCPUploadReceive(SocketServer.StreamRequestHandler):

    def handle(self):
        tempFile    = tmpDir + tmpFilePrefix + uuid.uuid4().hex
        done        = False
        f           = open(tempFile, 'w')
        http        = False
        bufferSize  = 4096
        index       = 0

        log(tempFile + " opened for writing.")
        log("Receiving file from {}...".format(self.client_address[0]))

        def finishHttp(good):
            if good:
                self.wfile.write('HTTP/1.1 200 OK\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
                self.request.close()
            else:
                self.wfile.write('{ "success": false, "message": "Bad mime type." }')
                f.close()
                log("Bad mime type detected on HTTP POST. Killing transfer.")

        while not done:
            if index > 0 and http:
                self.wfile.write('HTTP/1.1 100 Continue\r\n\r\n')

            bufferData = self.request.recv(bufferSize).strip()

            if index == 0 and checkHttp(bufferData):
                http = True
                index += 1
                continue

            if bufferData != "":
                f.write(bufferData)
                if http and len(bufferData) < bufferSize:
                    finishHttp(True)
                    break
            else:
                log('We have hit the done.')
                done = True

            index += 1
        f.close()

        unTarFile(tempFile, targetDir)
        rmFile(tempFile)

        self.wfile.write('{ "success": true }')
        log("Finished!\n")

            

def unTarFile(tarPath, target):
    log("Extracting...")
    with tarfile.open(tarPath, 'r|*') as tarball:
        tarball.extractall(target)

def rmFile(path):
    log("Removing temp file...")
    os.unlink(path)

def log(message):
    logTime = '%H:%M:%S%%%y-%m-%d - '
    sys.stdout.write(time.strftime(logTime))
    sys.stdout.write(message)
    sys.stdout.write('\n')
    sys.stdout.flush()


def checkHttp(bufferData):
    headMatch = '^POST.*HTTP.*'
    contMatch = "Content-type: application\/(x-gzip|x-tar|x-bz2|x-bzip|x-bzip2)"

    if re.search(headMatch, bufferData, re.I) and re.search(contMatch, bufferData, re.I | re.M):
        return True

    return False

if __name__ == "__main__":
    # Some environment fixing, before we begin:
    if not os.path.exists(tmpDir):
        os.makedirs(tmpDir)
    if not os.path.exists(targetDir):
        os.makedirs(targetDir)

    HOST, PORT = "0.0.0.0", 9999

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), TCPUploadReceive)
    log("Receiver now listening on port " + str(PORT))
    server.serve_forever()
