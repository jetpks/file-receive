#!/usr/bin/env python
import os
import sys
import SocketServer
import tarfile
import uuid
import time

#test
# Some globals:
tmpDir = './tmp/' # MUST END IN /
tmpFilePrefix = 'recvr-'
targetDir = '/tmp/mnt/sda1/tiles/' # ALSO MUST END IN /

class TCPUploadReceive(SocketServer.StreamRequestHandler):

    def handle(self):
        tempFile = tmpDir + tmpFilePrefix + uuid.uuid4().hex
        done = False
        f = open(tempFile, 'w')
        bufferSize = 4096

        log(tempFile + " opened for writing.")
        log("Receiving file from {}...".format(self.client_address[0]))

        while not done:
            bufferData = self.request.recv(bufferSize).strip()
            if bufferData != "":
                f.write(bufferData)
            else:
                done = True
        f.close()

        unTarFile(tempFile, targetDir)
        rmFile(tempFile)

        self.wfile.write('{ "success": "true" }')
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
