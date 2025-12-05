import React, { useEffect, useRef, useState } from "react"


const LogoIcon = () => (
  <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
    <path d="M6 6H12V20H26V26H6V6Z" fill="#22d3ee" /> {/* L */}
    <path d="M16 6H22V12H16V6Z" fill="white" /> {/* Dot */}
  </svg>
)

const MicIcon = ({ active }) => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={active ? "white" : "#9ca3af"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
    <line x1="12" y1="19" x2="12" y2="23" />
    <line x1="8" y1="23" x2="16" y2="23" />
  </svg>
)

const MessageIcon = ({ active }) => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={active ? "white" : "#9ca3af"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
)

const PhoneOffIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.68 13.31a16 16 0 0 0 3.41 2.6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7 2 2 0 0 1 1.72 2v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.42 19.42 0 0 1-3.33-2.67m-2.67-3.34a19.79 19.79 0 0 1-3.07-8.63A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91" />
    <line x1="23" y1="1" x2="1" y2="23" />
  </svg>
)

export default function App() {
  
  const wsRef = useRef(null)
  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const audioCtxRef = useRef(null)
  const playbackQueueRef = useRef([])
  const isPlayingRef = useRef(false)
  const sampleRateRef = useRef(24000)
  const analyserRef = useRef(null)
  const waveformCtxRef = useRef(null)
  const rafRef = useRef(null)

  const [status, setStatus] = useState("disconnected")
  const [messages, setMessages] = useState([])
  const [isRecording, setIsRecording] = useState(false)
  const [volume, setVolume] = useState(0)
  const [pendingText, setPendingText] = useState("")
  const [showTranscript, setShowTranscript] = useState(false) 

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8080/ws/voice")
    ws.binaryType = "arraybuffer"
    wsRef.current = ws
    ws.onopen = () => setStatus("connected")
    ws.onclose = () => setStatus("disconnected")

    ws.onmessage = async e => {
      if (typeof e.data === "string") {
        let msg
        try { msg = JSON.parse(e.data) } catch { return }

        if (msg.type === "user_transcript") {
          setPendingText("")
          setMessages(m => [...m, { from: "user", text: msg.text }])
        } else if (msg.type === "ai_text") {
          setPendingText("")
          setMessages(m => [...m, { from: "ai", text: msg.text }])
        } else if (msg.type === "error") {
          setMessages(m => [...m, { from: "system", text: `Error: ${msg.detail}` }])
          setPendingText("")
        } else if (msg.type === "audio_start") {
          if (msg.sampleRate) sampleRateRef.current = msg.sampleRate
        }
        return
      }
      let arrayBuf
      if (e.data instanceof ArrayBuffer) arrayBuf = e.data
      else if (e.data instanceof Blob) arrayBuf = await e.data.arrayBuffer()
      else return
      enqueueAudio(arrayBuf)
    }

    return () => {
      ws.close()
      stopPlayback()
      stopWaveform()
    }
  }, [])

  
  const ensureAudioContext = async () => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)()
    }
    if (audioCtxRef.current.state === "suspended") await audioCtxRef.current.resume()
  }

  const enqueueAudio = async arrayBuf => {
    await ensureAudioContext()
    playbackQueueRef.current.push(arrayBuf)
    if (!isPlayingRef.current) playNextChunk()
  }

  const playNextChunk = async () => {
    if (playbackQueueRef.current.length === 0) {
      isPlayingRef.current = false
      return
    }
    isPlayingRef.current = true
    await ensureAudioContext()
    const buffer = playbackQueueRef.current.shift()
    const ctx = audioCtxRef.current
    try {
      const pcm = new Int16Array(buffer)
      const float = new Float32Array(pcm.length)
      for (let i = 0; i < pcm.length; i++) float[i] = pcm[i] / 32768
      const audioBuf = ctx.createBuffer(1, float.length, sampleRateRef.current)
      audioBuf.getChannelData(0).set(float)
      const src = ctx.createBufferSource()
      src.buffer = audioBuf
      src.connect(ctx.destination)
      src.onended = playNextChunk
      src.start()
    } catch { playNextChunk() }
  }

  const stopPlayback = async () => {
    if (audioCtxRef.current) {
      try { await audioCtxRef.current.close() } catch { }
      audioCtxRef.current = null
    }
    playbackQueueRef.current = []
    isPlayingRef.current = false
  }

  const startWaveform = stream => {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const source = ctx.createMediaStreamSource(stream)
    const analyser = ctx.createAnalyser()
    analyser.fftSize = 2048
    source.connect(analyser)
    waveformCtxRef.current = ctx
    analyserRef.current = analyser
    const dataArray = new Uint8Array(analyser.frequencyBinCount)
    const tick = () => {
      if (!analyserRef.current) return
      analyserRef.current.getByteTimeDomainData(dataArray)
      let sum = 0
      for (let i = 0; i < dataArray.length; i++) {
        const v = (dataArray[i] - 128) / 128
        sum += v * v
      }
      setVolume(Math.sqrt(sum / dataArray.length))
      rafRef.current = requestAnimationFrame(tick)
    }
    tick()
  }

  const stopWaveform = async () => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current)
    if (waveformCtxRef.current) {
      try { await waveformCtxRef.current.close() } catch { }
    }
    waveformCtxRef.current = null
    analyserRef.current = null
    setVolume(0)
  }

  const interruptPlayback = async () => { await stopPlayback() }

  const startRecording = async () => {
    if (isRecording) return
    await interruptPlayback()
    setIsRecording(true)
    setPendingText("Listening...")
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    streamRef.current = stream
    startWaveform(stream)
    const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" })
    recorderRef.current = recorder
    recorder.ondataavailable = e => {
      if (wsRef.current?.readyState === 1 && e.data.size > 0) {
        e.data.arrayBuffer().then(buf => wsRef.current.send(buf))
      }
    }
    recorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop())
      stopWaveform()
      setIsRecording(false)
      setPendingText("Processing...")
    }
    recorder.start()
  }

  const stopRecording = () => {
    if (!isRecording) return
    if (recorderRef.current.state !== "inactive") recorderRef.current.stop()
  }

  

  
  const lastMessage = messages.length > 0 ? messages[messages.length - 1] : null

  
  
  const barHeight = (multiplier) => Math.max(10, Math.min(100, volume * 300 * multiplier)) + "px"

  return (
    <div style={{
      background: "#050505",
      color: "white",
      fontFamily: "'Inter', sans-serif",
      height: "100vh",
      width: "100vw",
      display: "flex",
      flexDirection: "column",
      overflow: "hidden"
    }}>



      {/* 2. Main Stage (Visualizer + Captions) */}
      <main style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        position: "relative"
      }}>

        {/* Floating Chat/Transcript Overlay (Toggled) */}
        {showTranscript && (
          <div style={{
            position: "absolute", top: 20, right: 40, width: "300px", bottom: 100,
            background: "rgba(20,20,20, 0.9)", border: "1px solid #333", borderRadius: "12px",
            padding: "20px", overflowY: "auto", zIndex: 10
          }}>
            <h3 style={{ marginTop: 0, fontSize: "14px", color: "#666" }}>TRANSCRIPT</h3>
            {messages.map((m, i) => (
              <div key={i} style={{ marginBottom: "12px", fontSize: "14px" }}>
                <strong style={{ color: m.from === "user" ? "#22d3ee" : "#a78bfa" }}>
                  {m.from === "user" ? "You" : "AI"}:
                </strong>
                <div style={{ color: "#ddd", marginTop: "4px" }}>{m.text}</div>
              </div>
            ))}
          </div>
        )}

        {/* Visualizer Bars */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", height: "120px" }}>
          {/* We create 5 bars with different sensitivities to simulate a waveform */}
          {[0.8, 1.5, 2.0, 1.5, 0.8].map((mult, i) => (
            <div key={i} style={{
              width: "24px",
              height: isRecording || isPlayingRef.current ? barHeight(mult) : "24px",
              background: "white",
              borderRadius: "99px",
              transition: "height 0.05s ease",
              boxShadow: (isRecording || isPlayingRef.current) ? "0 0 15px rgba(255,255,255,0.6)" : "none"
            }} />
          ))}
        </div>

        {/* Captions */}
        <div style={{
          marginTop: "60px",
          textAlign: "center",
          maxWidth: "600px",
          minHeight: "60px",
          padding: "0 20px"
        }}>
          {pendingText ? (
            <span style={{ color: "#888", fontStyle: "italic" }}>{pendingText}</span>
          ) : lastMessage ? (
            <span style={{ fontSize: "24px", fontWeight: "500", lineHeight: "1.4" }}>
              {lastMessage.text}
            </span>
          ) : (
            <span style={{ color: "#444" }}>Ready to chat...</span>
          )}
        </div>

      </main>

      {/* 3. Bottom Control Bar */}
      <footer style={{
        display: "flex",
        justifyContent: "center",
        paddingBottom: "40px"
      }}>
        <div style={{
          background: "#18181b",
          border: "1px solid #27272a",
          borderRadius: "999px",
          padding: "8px 16px",
          display: "flex",
          gap: "8px",
          alignItems: "center"
        }}>

          {/* Mic / PTT Button */}
          <button
            onMouseDown={startRecording}
            onMouseUp={stopRecording}
            onMouseLeave={stopRecording}
            onTouchStart={startRecording}
            onTouchEnd={stopRecording}
            style={{
              background: isRecording ? "#ef4444" : "#27272a",
              border: "none",
              width: "48px", height: "48px", borderRadius: "50%",
              display: "flex", alignItems: "center", justifyContent: "center",
              cursor: "pointer",
              transition: "all 0.2s"
            }}
            title="Hold to Talk"
          >
            <MicIcon active={isRecording} />
          </button>

          {/* Transcript Toggle */}
          <button
            onClick={() => setShowTranscript(!showTranscript)}
            style={{
              background: showTranscript ? "#3f3f46" : "transparent",
              border: "none",
              width: "48px", height: "48px", borderRadius: "50%",
              display: "flex", alignItems: "center", justifyContent: "center",
              cursor: "pointer"
            }}
          >
            <MessageIcon active={showTranscript} />
          </button>

          {/* End Call (Just disconnects socket for now) */}
          <button
            onClick={() => wsRef.current?.close()}
            style={{
              background: "#7f1d1d",
              border: "none",
              marginLeft: "12px",
              padding: "0 24px", height: "48px", borderRadius: "99px",
              display: "flex", alignItems: "center", justifyContent: "center",
              cursor: "pointer",
              color: "white",
              fontWeight: "600",
              fontSize: "14px",
              gap: "8px"
            }}
          >
            <PhoneOffIcon />
            <span>End Call</span>
          </button>
        </div>
      </footer>
    </div>
  )
}