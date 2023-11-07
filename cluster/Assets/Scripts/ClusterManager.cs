using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class ClusterManager : MonoBehaviour
{
    public GameObject messageObject;
    public GameObject voiceeObject;
    public GameObject touchObject;
    public Light directionalLight;
    public List<GameObject> Cabins = new List<GameObject>(new GameObject[4]);
    public List<Vector3> CabinPositions = new List<Vector3>(new Vector3[4]);

    private ReceiveSkeleton _SkeletonReceiver;
    private SkeletonData _SkeletonData;
    private VoiceData _VoiceData;
    private bool _IsUpdated = false;
    private bool _IsVoiceUpdated = false;
    private List<int> _CabinCount = new List<int>(new int[4]);
    private TMP_Text _messageText;
    private TMP_Text _voiceText;
    private TouchManager _touchManager;

    void Start()
    {
        _messageText = messageObject.GetComponent<TMP_Text>();
        _voiceText = voiceeObject.GetComponent<TMP_Text>();
        _touchManager = touchObject.GetComponent<TouchManager>();
        _touchManager.SetTouchCallback(new CallbackTouch(TouchHandler));
        // directionalLight.intensity = 4.0f;

        _messageText.text = "";
        _voiceText.text = "";
        _SkeletonReceiver = new ReceiveSkeleton("127.0.0.1", 50002);
        _SkeletonReceiver.Initialize();
        _SkeletonReceiver.SetSkeletonCallback(new CallbackSkeleton(ReceiveSkeletonData));
        _SkeletonReceiver.SetVoiceCallback(new CallbackVoice(ReceiveVoiceData));

        for (int i = 0; i < Cabins.Count; i++) {
            Cabins[i].SetActive(false);
            CabinPositions[i] = Cabins[i].transform.position;
        }
    }

    void Update()
    {
        if (_IsUpdated) {
            UpdateCluster(_SkeletonData);
        }
        if (_IsVoiceUpdated) {
            StartCoroutine(ShowTextForSeconds(_VoiceData.voice, 3.0f));
            _IsVoiceUpdated = false;
        }
    }

    void UpdateCluster(SkeletonData skeleton_data) {
        int id = skeleton_data.id;
        int status = skeleton_data.status;
        int control = skeleton_data.control;
        List<List<double>> skeleton = skeleton_data.skeleton;

        if(id == 0) { // Driver
            if(status == 1) {
                _messageText.text = "정상 운행 중";
            } else if (status == 2 || status == 3) {
                _messageText.text = "운전 부주의";
            }
        }

        if (skeleton[5][2] > 0.3 && skeleton[6][2] > 0.3) { // Left and Right Shoulder
            if (Cabins[id].activeSelf == false) {
                Cabins[id].SetActive(true);
                Cabins[id].transform.position = CabinPositions[id];
            }
            _CabinCount[id] = 0;
        } else {
            if (_CabinCount[id] > 60 * 3) {
                Cabins[id].SetActive(false);
            }
            _CabinCount[id] += 1;
        }

        // Reset skeleton data
        for (int i = 0; i < 11; i++) {
            skeleton_data.skeleton[i][2] = 0;
        }
    }

    void ReceiveSkeletonData(SkeletonData skeleton_data) {
        _SkeletonData = skeleton_data;
        _IsUpdated = true;
    }

    void ReceiveVoiceData(VoiceData voice_data) {
        _VoiceData = voice_data;
        if (_VoiceData.id == 0) {
            _IsVoiceUpdated = true;
        }
    }

    IEnumerator ShowTextForSeconds(string text, float seconds)
    {
        if (text == "error") {
            text = "음성 인식에 실패했습니다";
        }
        _voiceText.text = text;
        yield return new WaitForSeconds(seconds);
        _voiceText.text = "";
    }

    void TouchHandler() {
        Debug.Log("[ClusterManager] Touch");
        _SkeletonReceiver.SendDriverMessage();
    }
}
