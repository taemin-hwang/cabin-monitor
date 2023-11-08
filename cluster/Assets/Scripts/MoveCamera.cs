using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

public class MoveCamera : MonoBehaviour
{
    // public GameObject target;
    private float xRotateMove;
    public float rotateSpeed = 500.0f;

    public Vector3 target_pos;

    void Start(){
        StartCoroutine(RotateAroundTarget(8f));
    }

    void Update(){
        Rotate();
    }

    private void Rotate(){
        if (Input.GetMouseButton(0)){
            xRotateMove = Input.GetAxis("Mouse X") * Time.deltaTime * rotateSpeed;
            transform.RotateAround(target_pos, Vector3.up, xRotateMove);
        }
    }

    IEnumerator RotateAroundTarget(float duration)
    {
        Vector3 axis = Vector3.up; // 회전 축 (여기서는 위쪽을 기준으로 회전)
        float rotationSpeed = 360f / duration; // 회전 속도 계산

        float totalRotation = 0f; // 회전한 총 각도
        while (totalRotation < 360f)
        {
            float step = rotationSpeed * Time.deltaTime; // 이번 프레임에서 회전할 각도
            transform.RotateAround(target_pos, axis, step); // 회전 실행
            totalRotation += step; // 회전한 각도 업데이트
            yield return null; // 다음 프레임까지 기다림
        }
    }
}
