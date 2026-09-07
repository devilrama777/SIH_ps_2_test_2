using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace MineIntel
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            try
            {
                // Determine base application directory
                string appDir = AppDomain.CurrentDomain.BaseDirectory;
                
                // 1. Locate pythonw.exe (windowless python runner) or python.exe
                string pythonw = null;
                
                string venvPythonw = Path.Combine(appDir, ".venv", "Scripts", "pythonw.exe");
                string venvPython = Path.Combine(appDir, ".venv", "Scripts", "python.exe");
                string sysPythonw = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python312", "pythonw.exe");
                string sysPython = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python312", "python.exe");

                if (File.Exists(venvPythonw))
                    pythonw = venvPythonw;
                else if (File.Exists(sysPythonw))
                    pythonw = sysPythonw;
                else if (File.Exists(venvPython))
                    pythonw = venvPython;
                else if (File.Exists(sysPython))
                    pythonw = sysPython;
                else
                    pythonw = "pythonw.exe";

                // 2. Configure background execution without console window
                ProcessStartInfo startInfo = new ProcessStartInfo
                {
                    FileName = pythonw,
                    Arguments = "-m apps.desktop.desktop_app",
                    WorkingDirectory = appDir,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WindowStyle = ProcessWindowStyle.Hidden
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
