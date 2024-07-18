from flask import Flask, request, jsonify, render_template
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaRecorder

app = Flask(__name__)
pcs = set()
recorders = {}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/offer', methods=["POST"])
async def offer():
    params = request.json
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("iceConnectionStateChange")
    async def on_iceConnectionStateChange():
        print(f"ICE connection state is {pc.iceConnectionState}")
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        print(f"Track {track.kind} received")

        if track.kind == "video":
            recorder = MediaRecorder("received_video.mp4")
            recorder.addTrack(track)
            asyncio.ensure_future(recorder.start())
            recorders[pc] = recorder

        @track.on("ended")
        async def on_ended():
            print(f"Track {track.kind} ended")
            await recorder.stop()
            del recorders

        print(f"Track {track.kind} started")

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return jsonify({
        'sdp': pc.localDescription.sdp,
        'type': pc.localDescription.type
    })


@app.route('/candidate', methods=["POST"])
async def candidate():
    params = request.json
    if not pcs:
        return 'No active peer connections', 400

    candidate = RTCIceCandidate(
        sdpMid=params["sdpMid"],
        sdpMLineIndex=params["sdpMLineIndex"],
        protocol=params['candidate'].split()[2],
        component=1,
        foundation=params['candidate'].split()[0].split(':')[1],
        ip=params['candidate'].split(':')[1].split()[4],
        port=int(params['candidate'].split()[5]),
        type=params['candidate'].split()[7],
        priority=int(params['candidate'].split()[3]),
        )
    pc = next(iter(pcs))

    await pc.addIceCandidate(candidate)
    return "ok"


@app.route("/shutdown", methods=["POST"])
async def shutdown():
    global pcs
    for pc in pcs:
        await pc.close()
        if pc in recorders.keys():
            recorders[pc].stop()
            del recorders[pc]
    pcs = set()
    return "ok"


if __name__ == '__main__':
    app.run(debug=True)