using System;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Media;
using DisabilityMapper.Services;
using Newtonsoft.Json.Linq;

namespace DisabilityMapper
{
    public partial class OfficeSuiteWindow : Window
    {
        private static OfficeSuiteWindow? _instance;
        private readonly string _docsFolder;

        public OfficeSuiteWindow()
        {
            InitializeComponent();
            _docsFolder = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
                "SARA_Documents");
            Directory.CreateDirectory(_docsFolder);

            Loaded += async (_, _) => await CheckSaraAndFatigue();
        }

        public static void Toggle()
        {
            if (_instance is { IsVisible: true })
            {
                _instance.Hide();
            }
            else
            {
                _instance ??= new OfficeSuiteWindow();
                _instance.Show();
                _instance.Activate();
                _instance.InputBox.Focus();
            }
        }

        protected override void OnClosed(EventArgs e)
        {
            _instance = null;
            base.OnClosed(e);
        }

        private async Task CheckSaraAndFatigue()
        {
            bool alive = await BuceyShunt.IsAlive();
            SaraDot.Fill = alive ? Brushes.Lime : Brushes.Red;
            StatusText.Text = alive ? "SARA connected" : "SARA offline — run SARA_RUN.bat";

            if (alive)
            {
                var bio = await BuceyShunt.Dispatch("biometric_status", "00", new JObject());
                var result = bio["result"] as JObject;
                string color = result?.Value<string>("fatigue_color") ?? "green";
                FatigueBar.Background = color switch
                {
                    "red" => Brushes.Red,
                    "yellow" => Brushes.Yellow,
                    _ => Brushes.Lime,
                };
            }
        }

        private async void AskSara_Click(object sender, RoutedEventArgs e)
        {
            string prompt = InputBox.Text.Trim();
            if (string.IsNullOrEmpty(prompt)) return;

            AskBtn.IsEnabled = false;
            StatusText.Text = "Thinking...";
            ResponseBox.Text = "";

            try
            {
                var payload = new JObject { ["prompt"] = prompt };
                var result = await BuceyShunt.Dispatch("ai_generate", "11", payload);

                var inner = result["result"] as JObject;
                string text = inner?.Value<string>("text") ?? result.Value<string>("error") ?? "No response";
                ResponseBox.Text = text;
                StatusText.Text = "Done";
            }
            catch (Exception ex)
            {
                ResponseBox.Text = $"Error: {ex.Message}";
                StatusText.Text = "Error";
            }
            finally
            {
                AskBtn.IsEnabled = true;
            }
        }

        private async void SaveDocx_Click(object sender, RoutedEventArgs e)
        {
            string text = GetSaveText();
            if (string.IsNullOrEmpty(text)) return;

            string path = Path.Combine(_docsFolder, $"sara_{DateTime.Now:yyyyMMdd_HHmmss}.docx");
            var paragraphs = new JArray(text.Split('\n', StringSplitOptions.RemoveEmptyEntries));
            var payload = new JObject
            {
                ["output_path"] = path,
                ["paragraphs"] = paragraphs,
                ["title"] = "SARA Document"
            };
            var result = await BuceyShunt.Dispatch("write_docx", "10", payload);
            ShowSaveResult(result, path);
        }

        private async void SaveXlsx_Click(object sender, RoutedEventArgs e)
        {
            string text = GetSaveText();
            if (string.IsNullOrEmpty(text)) return;

            string path = Path.Combine(_docsFolder, $"sara_{DateTime.Now:yyyyMMdd_HHmmss}.xlsx");
            var rows = new JArray();
            foreach (var line in text.Split('\n', StringSplitOptions.RemoveEmptyEntries))
            {
                var cells = new JArray(line.Split('\t', ','));
                rows.Add(cells);
            }
            var payload = new JObject
            {
                ["output_path"] = path,
                ["sheets"] = new JObject { ["Sheet1"] = rows }
            };
            var result = await BuceyShunt.Dispatch("write_xlsx", "10", payload);
            ShowSaveResult(result, path);
        }

        private async void SavePdf_Click(object sender, RoutedEventArgs e)
        {
            string text = GetSaveText();
            if (string.IsNullOrEmpty(text)) return;

            string path = Path.Combine(_docsFolder, $"sara_{DateTime.Now:yyyyMMdd_HHmmss}.pdf");
            var lines = new JArray(text.Split('\n', StringSplitOptions.RemoveEmptyEntries));
            var payload = new JObject
            {
                ["output_path"] = path,
                ["lines"] = lines,
                ["title"] = "SARA Document"
            };
            var result = await BuceyShunt.Dispatch("write_pdf", "10", payload);
            ShowSaveResult(result, path);
        }

        private async void DraftDocx_Click(object sender, RoutedEventArgs e)
        {
            string prompt = InputBox.Text.Trim();
            if (string.IsNullOrEmpty(prompt)) return;

            AskBtn.IsEnabled = false;
            StatusText.Text = "Drafting document...";

            string path = Path.Combine(_docsFolder, $"sara_draft_{DateTime.Now:yyyyMMdd_HHmmss}.docx");
            var payload = new JObject
            {
                ["prompt"] = prompt,
                ["output_path"] = path,
                ["title"] = "SARA Draft"
            };

            try
            {
                var result = await BuceyShunt.Dispatch("ai_draft_docx", "10", payload);
                var inner = result["result"] as JObject;
                bool ok = inner?.Value<bool>("success") ?? false;
                if (ok)
                {
                    ResponseBox.Text = $"Document saved to:\n{path}";
                    SaveStatus.Text = $"Saved: {path}";
                }
                else
                {
                    ResponseBox.Text = $"Draft failed: {inner?.Value<string>("error") ?? "unknown"}";
                }
            }
            catch (Exception ex)
            {
                ResponseBox.Text = $"Error: {ex.Message}";
            }
            finally
            {
                AskBtn.IsEnabled = true;
                StatusText.Text = "Done";
            }
        }

        private async void WebBrowse_Click(object sender, RoutedEventArgs e)
        {
            string url = InputBox.Text.Trim();
            if (string.IsNullOrEmpty(url)) return;
            if (!url.StartsWith("http")) url = "https://" + url;

            StatusText.Text = "Browsing...";
            var payload = new JObject { ["url"] = url, ["extract"] = "text" };
            var result = await BuceyShunt.Dispatch("web_browse", "00", payload);
            var inner = result["result"] as JObject;
            ResponseBox.Text = inner?.Value<string>("text") ?? inner?.Value<string>("error") ?? "No response";
            StatusText.Text = "Done";
        }

        private async void WebSearch_Click(object sender, RoutedEventArgs e)
        {
            string query = InputBox.Text.Trim();
            if (string.IsNullOrEmpty(query)) return;

            StatusText.Text = "Searching...";
            var payload = new JObject { ["query"] = query, ["num_results"] = 8 };
            var result = await BuceyShunt.Dispatch("web_search", "00", payload);
            var inner = result["result"] as JObject;
            var results = inner?["results"] as JArray;
            if (results != null)
            {
                var lines = new System.Text.StringBuilder();
                foreach (JObject r in results)
                    lines.AppendLine($"{r.Value<string>("title")}\n  {r.Value<string>("url")}\n");
                ResponseBox.Text = lines.ToString();
            }
            else
            {
                ResponseBox.Text = inner?.Value<string>("error") ?? "No results";
            }
            StatusText.Text = "Done";
        }

        private async void SendEmail_Click(object sender, RoutedEventArgs e)
        {
            string text = EmailBox.Text.Trim();
            if (string.IsNullOrEmpty(text))
            {
                CommResponseBox.Text = "Format:  recipient@email.com | Subject | Message body";
                return;
            }

            var parts = text.Split('|');
            if (parts.Length < 3)
            {
                CommResponseBox.Text = "Format:  recipient@email.com | Subject | Message body";
                return;
            }

            StatusText.Text = "Sending email...";
            var emailData = new JObject
            {
                ["to"] = parts[0].Trim(),
                ["from"] = "",
                ["subject"] = parts[1].Trim(),
                ["body"] = parts[2].Trim()
            };
            var payload = new JObject { ["email_data"] = emailData };
            var result = await BuceyShunt.Dispatch("send_email", "11", payload);
            var inner = result["result"] as JObject;
            string status = inner?.Value<string>("status") ?? "UNKNOWN";
            CommResponseBox.Text = status == "PASS" ? "Email sent!" : $"Email failed: {inner?.Value<string>("error") ?? status}";
            StatusText.Text = "Done";
        }

        private async void CalendarList_Click(object sender, RoutedEventArgs e)
        {
            StatusText.Text = "Loading calendar...";
            var payload = new JObject { ["max_results"] = 10 };
            var result = await BuceyShunt.Dispatch("calendar_list", "00", payload);
            var inner = result["result"] as JObject;
            var events = inner?["events"] as JArray;
            if (events != null)
            {
                var lines = new System.Text.StringBuilder();
                foreach (JObject ev in events)
                {
                    lines.AppendLine($"{ev.Value<string>("start")}  {ev.Value<string>("summary")}");
                    string loc = ev.Value<string>("location") ?? "";
                    string meet = ev.Value<string>("meet_link") ?? "";
                    if (!string.IsNullOrEmpty(loc)) lines.AppendLine($"  Location: {loc}");
                    if (!string.IsNullOrEmpty(meet)) lines.AppendLine($"  Meet: {meet}");
                    lines.AppendLine();
                }
                CommResponseBox.Text = lines.ToString();
            }
            else
            {
                CommResponseBox.Text = inner?.Value<string>("error") ?? "No events or calendar not configured";
            }
            StatusText.Text = "Done";
        }

        private void Clear_Click(object sender, RoutedEventArgs e)
        {
            InputBox.Text = "";
            ResponseBox.Text = "";
            SaveStatus.Text = "";
            InputBox.Focus();
        }

        // ── Python IDE handlers ──────────────────────────────────────────────

        private async void RunPython_Click(object sender, RoutedEventArgs e)
        {
            string code = PyEditorBox.Text.Trim();
            if (string.IsNullOrEmpty(code)) return;

            RunBtn.IsEnabled = false;
            PyStatusText.Text = "Running...";
            PyOutputBox.Text = "";

            try
            {
                var payload = new JObject { ["code"] = code };
                var result = await BuceyShunt.Dispatch("python_run", "10", payload);
                var inner = result["result"] as JObject;

                var sb = new System.Text.StringBuilder();
                string stdout = inner?.Value<string>("stdout") ?? "";
                string stderr = inner?.Value<string>("stderr") ?? "";
                string error  = inner?.Value<string>("error")  ?? "";

                if (!string.IsNullOrEmpty(stdout)) sb.AppendLine(stdout);
                if (!string.IsNullOrEmpty(stderr)) sb.AppendLine("--- stderr ---").AppendLine(stderr);
                if (!string.IsNullOrEmpty(error))  sb.AppendLine($"Error: {error}");
                if (sb.Length == 0) sb.AppendLine("(no output)");

                PyOutputBox.Text = sb.ToString();
                bool ok = inner?.Value<bool>("success") ?? false;
                PyStatusText.Text = ok ? "Done" : "Finished with errors";
                PyStatusText.Foreground = ok
                    ? new SolidColorBrush(System.Windows.Media.Color.FromRgb(0x1B, 0xA0, 0x5E))
                    : new SolidColorBrush(System.Windows.Media.Color.FromRgb(0xC0, 0x39, 0x2B));
            }
            catch (Exception ex)
            {
                PyOutputBox.Text = $"Error: {ex.Message}";
                PyStatusText.Text = "Error";
            }
            finally
            {
                RunBtn.IsEnabled = true;
            }
        }

        private void ClearPython_Click(object sender, RoutedEventArgs e)
        {
            PyEditorBox.Text = "";
            PyOutputBox.Text = "";
            PyStatusText.Text = "";
            PyEditorBox.Focus();
        }

        private void OpenPyFile_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new Microsoft.Win32.OpenFileDialog
            {
                Filter = "Python files (*.py)|*.py|All files (*.*)|*.*",
                Title = "Open Python script"
            };
            if (dlg.ShowDialog() == true)
            {
                PyEditorBox.Text = System.IO.File.ReadAllText(dlg.FileName);
                PyStatusText.Text = $"Opened: {System.IO.Path.GetFileName(dlg.FileName)}";
            }
        }

        private void SavePyFile_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new Microsoft.Win32.SaveFileDialog
            {
                Filter = "Python files (*.py)|*.py|All files (*.*)|*.*",
                Title = "Save Python script",
                FileName = $"script_{DateTime.Now:yyyyMMdd_HHmmss}.py"
            };
            if (dlg.ShowDialog() == true)
            {
                System.IO.File.WriteAllText(dlg.FileName, PyEditorBox.Text);
                PyStatusText.Text = $"Saved: {System.IO.Path.GetFileName(dlg.FileName)}";
            }
        }

        // ── Communication app launchers ──────────────────────────────────────

        private void OpenTeams_Click(object sender, RoutedEventArgs e)   => LaunchApp("ms-teams:",        "msteams.exe");
        private void OpenZoom_Click(object sender, RoutedEventArgs e)    => LaunchApp("zoommtg:",         "Zoom.exe");
        private void OpenSlack_Click(object sender, RoutedEventArgs e)   => LaunchApp("slack:",           "slack.exe");
        private void OpenOutlook_Click(object sender, RoutedEventArgs e) => LaunchApp("outlook:",         "OUTLOOK.EXE");

        private void LaunchApp(string uriScheme, string fallbackExe)
        {
            try
            {
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = uriScheme,
                    UseShellExecute = true
                });
            }
            catch
            {
                // URI scheme failed — try the executable name via shell
                try
                {
                    System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                    {
                        FileName = fallbackExe,
                        UseShellExecute = true
                    });
                }
                catch (Exception ex)
                {
                    StatusText.Text = $"App not found: {ex.Message}";
                }
            }
        }

        private string GetSaveText()
        {
            string text = ResponseBox.Text;
            if (string.IsNullOrWhiteSpace(text))
                text = InputBox.Text;
            if (string.IsNullOrWhiteSpace(text))
            {
                SaveStatus.Text = "Nothing to save — type or ask SARA first.";
                return "";
            }
            return text;
        }

        private void ShowSaveResult(JObject result, string path)
        {
            var inner = result["result"] as JObject;
            bool ok = inner?.Value<bool>("success") ?? false;
            SaveStatus.Text = ok
                ? $"Saved: {path}"
                : $"Save failed: {inner?.Value<string>("error") ?? result.Value<string>("error") ?? "unknown"}";
        }
    }
}
