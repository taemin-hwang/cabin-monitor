using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

public class MoveCamera : MonoBehaviour
{
    // public GameObject target;
    // private Camera mainCamera;
    private float xRotateMove, yRotateMove;
    public float rotateSpeed = 500.0f;
    public float zoomSpeed = 20.0f;
    public float maxRotationAngle = 90f;

    public bool isRotating = false;
    public float rotateSpeed2 = 500f;
    // private int currentRotationAngle = 0;

    public Vector3 target_pos;
    private Vector3 target_init = new Vector3(0.0f, 1.2f, 0f);

    private bool isTouched = false;
    private Vector3 initialPosition;
    private Vector3 initialRotation;
    private bool is_tracking = false;

    void Start(){
        // mainCamera = GetComponent<Camera>();
        initialPosition = transform.position;
        initialRotation = transform.eulerAngles;
        InitializeTarget();

        transform.LookAt(target_pos);
    }

    void Update(){
        Rotate();
    }

    public void InitializeTarget() {
        target_pos = target_init;
    }

    public void SetTracking(bool isOn) {
        is_tracking = isOn;
        if (!is_tracking) {
            InitializeTarget();
        }
    }

    public void UpdateTarget() {
        if (is_tracking) {
            GameObject target = GameObject.Find("character-03(Clone)");
            // Debug.Log("target.transform.position: " + target.transform.position);

            GameObject child = target.transform.Find("mixamorig9:Hips").gameObject;
            // Debug.Log("child.transform.position: " + child.transform.position);

            transform.position = new Vector3(child.transform.position.x, child.transform.position.y + 1.5f, child.transform.position.z + 5f);
            transform.LookAt(child.transform.position);
            isTouched = true;
        }
    }

    public void RotateLeft(){

        if (isTouched == true) {
            transform.position = initialPosition;
            transform.eulerAngles = initialRotation;
            isTouched = false;
        }

        transform.RotateAround(target_pos, Vector3.up, -90);
        transform.LookAt(target_pos);
    }

    public bool IsPointerOverUIObject(Vector2 touchPos)
    {
        // return false;
        PointerEventData eventDataCurrentPosition = new PointerEventData(EventSystem.current);
        eventDataCurrentPosition.position = touchPos;
        List<RaycastResult> results = new List<RaycastResult>();
        EventSystem.current.RaycastAll(eventDataCurrentPosition, results);
        return results.Count > 0;
    }

    private void Zoom(){
        float distance = Input.GetAxis("Mouse ScrollWheel") * -1 * zoomSpeed;
        if(distance != 0) {
            // mainCamera.fieldOfView += distance;
        }
    }

    private void Rotate(){
        if (Input.GetMouseButton(0)){
            // if(!IsPointerOverUIObject(Input.mousePosition)) {
                xRotateMove = Input.GetAxis("Mouse X") * Time.deltaTime * rotateSpeed;
                // yRotateMove = Input.GetAxis("Mouse Y") * Time.deltaTime * rotateSpeed;
                transform.RotateAround(target_pos, Vector3.up, xRotateMove);
                // transform.RotateAround(target_pos, Vector3.right, yRotateMove);

                // isTouched = true;

                // float cameraHeight = transform.position.y;
                // if (cameraHeight < 0f) {
                //     transform.position -= new Vector3(0f, cameraHeight, 0f);
                // }

                // transform.LookAt(target_pos);
            // }
        }
    }
}
