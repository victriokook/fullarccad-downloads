using System;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Diagnostics;
using System.Threading;
using System.Windows.Forms;
using System.Security.Cryptography;
[assembly: AssemblyTitle("FullArcCAD Portable")]
[assembly: AssemblyProduct("FullArcCAD")]
[assembly: AssemblyVersion("0.2.266.1")]
internal static class Portable {
    [STAThread] static int Main(string[] args) {
        Application.EnableVisualStyles();
        try {
            string digest;
            using(var data=Assembly.GetExecutingAssembly().GetManifestResourceStream("FullArcCAD.Payload.zip"))
            using(var sha=SHA256.Create())digest=BitConverter.ToString(sha.ComputeHash(data)).Replace("-","").ToLowerInvariant();
            string cache=Environment.GetEnvironmentVariable("FULLARCCAD_PORTABLE_CACHE")??Path.Combine(Common.Local,"FullArcCADPortable","cache");
            string root=Path.Combine(cache,digest);
            using(var mutex=new Mutex(false,@"Local\FullArcCADPortableExtract-"+digest)) {
                bool held=false;
                try {
                    try{held=mutex.WaitOne(60000);}catch(AbandonedMutexException){held=true;}
                    if(!held)throw new IOException("Extraction is busy. Please retry.");
                    string marker=Path.Combine(root,".complete");
                    if(!File.Exists(marker)) {
                        Directory.CreateDirectory(root);
                        using(var stream=Assembly.GetExecutingAssembly().GetManifestResourceStream("FullArcCAD.Payload.zip"))
                        using(var zip=new ZipArchive(stream,ZipArchiveMode.Read))
                        foreach(var entry in zip.Entries) {
                            if(entry.FullName.EndsWith("/"))continue;
                            string path=Common.SafePath(root,entry.FullName.Replace('/','\\'));
                            Directory.CreateDirectory(Path.GetDirectoryName(path));
                            using(var input=entry.Open())using(var output=new FileStream(path,FileMode.Create,FileAccess.Write))input.CopyTo(output);
                        }
                        File.WriteAllText(marker,digest);
                    }
                }finally{if(held)mutex.ReleaseMutex();}
            }
            string state=Environment.GetEnvironmentVariable("FULLARCCAD_STATE_DIR")??Path.Combine(Common.Base,"FullArcCAD-data");
            Directory.CreateDirectory(state);
            string command=string.Join(" ",Array.ConvertAll(args,Common.Quote));
            var start=new ProcessStartInfo(Path.Combine(root,"FullArcCAD.exe"),command){UseShellExecute=false,WorkingDirectory=root};
            start.EnvironmentVariables["FULLARCCAD_STATE_DIR"]=state;
            using(var p=Process.Start(start)){p.WaitForExit();return p.ExitCode;}
        }catch(Exception error){MessageBox.Show(error.Message,"FullArcCAD Portable",MessageBoxButtons.OK,MessageBoxIcon.Error);return 1;}
    }
}
