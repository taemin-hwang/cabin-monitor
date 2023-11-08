using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class ClusterManager : MonoBehaviour
{
    public GameObject messageObject;
    public GameObject voiceeObject;
    public GameObject touchObject;
    public GameObject clusterInfoObject;
    public Light directionalLight;
    public List<GameObject> Cabins = new List<GameObject>(new GameObject[4]);
    public List<Vector3> CabinPositions = new List<Vector3>(new Vector3[4]);
    public List<Vector3> TargetPositions = new List<Vector3>(new Vector3[4]);

    private ReceiveSkeleton _SkeletonReceiver;
    private SkeletonData _SkeletonData;
    private VoiceData _VoiceData;
    private bool _IsUpdated = false;
    private bool _IsVoiceUpdated = false;
    private List<int> _CabinCount = new List<int>(new int[4]);
    private TMP_Text _messageText;
    private TMP_Text _voiceText;
    private TouchManager _touchManager;

    private HMI.UI.Cluster.ClusterInfoController _clusterInfoController;

    void Start()
    {
        _messageText = messageObject.GetComponent<TMP_Text>();
        _voiceText = voiceeObject.GetComponent<TMP_Text>();
        _touchManager = touchObject.GetComponent<TouchManager>();
        _clusterInfoController = clusterInfoObject.GetComponent<HMI.UI.Cluster.ClusterInfoController>();
        _touchManager.SetTouchCallback(new CallbackTouch(TouchHandler));

        _messageText.text = "";
        _voiceText.text = "";
        _SkeletonReceiver = new ReceiveSkeleton("127.0.0.1", 50002);
        _SkeletonReceiver.Initialize();
        _SkeletonReceiver.SetSkeletonCallback(new CallbackSkeleton(ReceiveSkeletonData));
        _SkeletonReceiver.SetVoiceCallback(new CallbackVoice(ReceiveVoiceData));

        for (int i = 0; i < Cabins.Count; i++) {
            Cabins[i].SetActive(false);
            CabinPositions[i] = Cabins[i].transform.position;
            TargetPositions[i] = Cabins[i].GetComponent<DriverController>().target.position;
        }
    }

    void Update()
    {
        if (_IsUpdated) {
            UpdateCluster(_SkeletonData);
            _IsUpdated = false;
        }
        if (_IsVoiceUpdated) {
            StartCoroutine(ShowTextForSeconds(_VoiceData.voice, 3.0f));
            _IsVoiceUpdated = false;
        }
        RenderSettings.skybox.SetFloat("_Rotation", Time.time * 0.8f);
    }

    void UpdateCluster(SkeletonData skeleton_data) {
        int id = skeleton_data.id;
        int status = skeleton_data.status;
        int control = skeleton_data.control;
        int gaze = skeleton_data.gaze;
        List<List<double>> skeleton = skeleton_data.skeleton;

        if (gaze > 40) {
            gaze = 40;
        } else if (gaze < -40) {
            gaze = -40;
        }

        if(id == 0) { // Driver
            if(status == 1) {
                _messageText.text = "정상 운행 중";
                if(control == 3) {
                    Debug.Log("[ClusterManager] LEFT");
                    _clusterInfoController.Previous();
                } else if (control == 4) {
                    Debug.Log("[ClusterManager] RIGHT");
                    _clusterInfoController.Next();
                }
            } else if (status == 2 || status == 3) {
                _messageText.text = "운전 부주의";
            }
            UpdateGaze(id, Cabins[id], gaze);
        }

        if (skeleton[5][2] > 0.3 && skeleton[6][2] > 0.3) { // Left and Right Shoulder
            if (Cabins[id].activeSelf == false) {
                Cabins[id].SetActive(true);
                Cabins[id].transform.position = CabinPositions[id];
            }
            _CabinCount[id] = 0;
        } else {
            if (_CabinCount[id] > 60 * 10) {
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
            text = "다시 한 번 말씀해주세요";
        }

        if (text.Contains("어둡게")) {
            directionalLight.intensity = 1f;
        } else if (text.Contains("밝게")) {
            directionalLight.intensity = 2f;
        }

        _voiceText.text = text;
        yield return new WaitForSeconds(seconds);
        _voiceText.text = "";
    }

    void UpdateGaze(int id, GameObject cabin, int gaze) {
        DriverController controller = cabin.GetComponent<DriverController>();
        Transform target = controller.target;
        // target.localPosition = new Vector3(gaze / -40f, 1.3f, 0.5f);
        Vector3 target_position = new Vector3(TargetPositions[id].x, TargetPositions[id].y, gaze / -40f + TargetPositions[id].z);

        // Debug.Log("Initial Position: " + TargetPositions[id]);
        // Debug.Log("Target  Position: " + target_position);

        // Convert local Position to world Position

        target.position = Vector3.MoveTowards(target.position, target_position, 20f * Time.deltaTime);
    }

    void TouchHandler() {
        Debug.Log("[ClusterManager] Touch");
        _SkeletonReceiver.SendDriverMessage();
    }
}
