using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace MineIntel
{
    static class Program
    {
        [DllImport("shell32.dll", SetLastError = true)]
        private static extern void SetCurrentProcessExplicitAppUserModelID([MarshalAs(UnmanagedType.LPWStr)] string AppID);

        [STAThread]
        static void Main()
        {
            try
            {
                // Register Windows Application User Model ID for taskbar grouping and custom icon
                try
                {
                    SetCurrentProcessExplicitAppUserModelID("MineIntel.Corporate.Desktop.1.0");
                }
                catch { }

                // Determine base application directory
                string appDir = AppDomain.CurrentDomain.BaseDirectory;
                
                // 1. Locate pythonw.exe (windowless python runner) or python.exe
                string pythonw = null;
                
                string venvPythonw = Path.Combine(appDir, ".venv", "Scripts", "pythonw.exe");
                string venvPython = Path.Combine(appDir, ".venv", "Scripts", "python.exe");

                string[] candidatePaths = new string[]
                {
                    venvPythonw,
                    @"C:\Python314\pythonw.exe",
                    @"C:\Python313\pythonw.exe",
                    @"C:\Python312\pythonw.exe",
                    Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python314", "pythonw.exe"),
                    Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python313", "pythonw.exe"),
                    Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python312", "pythonw.exe"),
                    venvPython,
                    @"C:\Python314\python.exe",
                    @"C:\Python313\python.exe",
                    @"C:\Python312\python.exe",
                    Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python314", "python.exe"),
                    Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python313", "python.exe"),
                    Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python312", "python.exe"),
                };

                foreach (string candidate in candidatePaths)
                {
                    if (File.Exists(candidate))
                    {
                        pythonw = candidate;
                        break;
                    }
                }

                if (string.IsNullOrEmpty(pythonw))
                    pythonw = "pythonw.exe";

                // 2. Configure execution with visible window style for Edge WebView2 composition
                ProcessStartInfo startInfo = new ProcessStartInfo
                {
                    FileName = pythonw,
                    Arguments = "-m apps.desktop.desktop_app",
                    WorkingDirectory = appDir,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WindowStyle = ProcessWindowStyle.Normal
                };

                using (Process proc = Process.Start(startInfo))
                {
                    if (proc != null)
                    {
                        proc.WaitForExit();
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    "Error starting MineIntel: " + ex.Message,
                    "MineIntel Launch Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
            }
        }
    }
}
