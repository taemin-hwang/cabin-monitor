using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;
using System.Net;
using System.Net.Sockets;
//using System.Text;
using System.Threading;
using Newtonsoft.Json;

[System.Serializable]
public class SkeletonData
{
    public int id { get; set; }
    public int type { get; set; }
    public int status { get; set; }
    public int control { get; set; }
    public int gaze { get; set; }
    public List<List<double>> skeleton = new List<List<double>>();
}

public class VoiceData
{
    public int id { get; set; }
    public int type { get; set; }
    public string voice { get; set; }
}

public delegate void CallbackSkeleton(SkeletonData message);
public delegate void CallbackVoice(VoiceData message);

public class ReceiveSkeleton
{
    public string _IpAddr = "127.0.0.1";
    public int _Port = 50002;

    private string _DriverIpAddr = "";
    private int _DriverPort = -1;
    CallbackSkeleton _CallbackSkeleton;
    CallbackVoice _CallbackVoice;

    #region private members
    private Thread ListenerThread;
    #endregion

    public ReceiveSkeleton(string IpAddr, int Port) {
        _IpAddr = IpAddr;
        _Port = Port;
    }

    public void Initialize() {
        // Start TcpServer background thread
        ListenerThread = new Thread(new ThreadStart(ListenForIncommingRequest));
        ListenerThread.IsBackground = true;
        ListenerThread.Start();
    }

    void ListenForIncommingRequest() {
        Debug.Log("Start Server : " + _IpAddr + ", " + _Port);
        UdpClient listener = new UdpClient(_Port);
        IPEndPoint groupEP = new IPEndPoint(IPAddress.Any, _Port);
        try {
            while (true){
                byte[] bytes = listener.Receive(ref groupEP);

                string JsonString = Encoding.UTF8.GetString(bytes);

                SkeletonData JsonData = Newtonsoft.Json.JsonConvert.DeserializeObject<SkeletonData>(JsonString);
                if (JsonData.type == 0) {
                    SkeletonHandler(JsonData);
                    if (JsonData.id == 0) {
                        // client port number
                        Debug.Log("client port number : " + groupEP.Port);
                        _DriverPort = groupEP.Port;
                        _DriverIpAddr = groupEP.Address.ToString();
                    }
                } else if (JsonData.type == 1) { // voice
                    VoiceData VoiceData = Newtonsoft.Json.JsonConvert.DeserializeObject<VoiceData>(JsonString);
                    Debug.Log("ID : "+ VoiceData.id);
                    Debug.Log("Voice : "+ VoiceData.voice);
                    VoiceHandler(VoiceData);
                }
            }
        } catch (SocketException e) {
            Debug.Log("SocketException " + e.ToString());
        } finally {
            listener.Close();
        }
    }

    public int SendDriverMessage() {
        if (_DriverPort == -1) {
            Debug.Log("Driver port is not set");
            return -1;
        }
        Debug.Log("Send STT Request : " + _DriverIpAddr + ", " + _DriverPort);
        UdpClient client = new UdpClient();
        IPEndPoint ep = new IPEndPoint(IPAddress.Parse(_DriverIpAddr), _DriverPort);
        byte[] sendBytes = Encoding.UTF8.GetBytes("stt");
        client.Send(sendBytes, sendBytes.Length, ep);
        client.Close();
        return 0;
    }

    public void SetSkeletonCallback(CallbackSkeleton callback)
    {
        if (_CallbackSkeleton == null) {
            _CallbackSkeleton = callback;
        } else {
            _CallbackSkeleton += callback;
        }
    }

    public void SetVoiceCallback(CallbackVoice callback)
    {
        if (_CallbackVoice == null) {
            _CallbackVoice = callback;
        } else {
            _CallbackVoice += callback;
        }
    }

    private void SkeletonHandler(SkeletonData JsonData)
    {
        if (_CallbackSkeleton != null) {
            _CallbackSkeleton(JsonData);
        }
    }

    private void VoiceHandler(VoiceData JsonData)
    {
        if (_CallbackVoice != null) {
            _CallbackVoice(JsonData);
        }
    }
}
