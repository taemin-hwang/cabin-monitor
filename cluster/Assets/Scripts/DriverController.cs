using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class DriverController : MonoBehaviour
{
    public Animator anim;
    public Transform target;

    // Start is called before the first frame update
    void Start()
    {

    }

    void Update()
    {

    }

    void OnAnimatorIK()
    {
        anim.SetLookAtWeight(1.0f);
        anim.SetLookAtPosition(target.position);
    }
}
