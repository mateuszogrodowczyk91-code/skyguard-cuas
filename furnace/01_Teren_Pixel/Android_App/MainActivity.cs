using System;
using Android.App;
using Android.OS;

namespace SkyGuard.Tactical
{
    [Activity(Label = "SKYGUARD Tactical", MainLauncher = true, Icon = "@mipmap/icon")]
    public class MainActivity : Activity
    {
        protected override void OnCreate(Bundle? savedInstanceState)
        {
            base.OnCreate(savedInstanceState);
            Console.WriteLine("[SKYGUARD] Tactical Android App Started on Pixel 10 Pro!");
        }
    }
}
