using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// Raw Bucey Shunt dispatch — no wrappers, just envelope + POST.
    /// Speaks the same 8-field protocol every SARA pillar uses.
    /// </summary>
    public static class BuceyShunt
    {
        private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(120) };
        private const string Endpoint = "http://127.0.0.1:5050/shunt";

        /// <summary>
        /// Build a Bucey Shunt envelope. This is the universal SARA packet.
        /// ACT codes: 00=route, 01=validate/normalize, 10=build/office, 11=dispatch/audit
        /// </summary>
        public static JObject Envelope(
            string intent,
            string act,
            JObject payload,
            string sourcePillar = "MAMA",
            string targetPillar = "CONTROL")
        {
            return new JObject
            {
                ["shunt_id"]         = Guid.NewGuid().ToString(),
                ["source_pillar"]    = sourcePillar,
                ["target_pillar"]    = targetPillar,
                ["timestamp"]        = DateTime.UtcNow.ToString("o"),
                ["intent"]           = intent,
                ["ACT"]              = act,
                ["payload"]          = payload,
                ["context_tags"]     = new JArray(),
                ["requires_response"] = true
            };
        }

        /// <summary>Send a shunt envelope to CONTROL. Returns the raw JSON result.</summary>
        public static async Task<JObject> Send(JObject envelope)
        {
            try
            {
                var body = new StringContent(envelope.ToString(), Encoding.UTF8, "application/json");
                var resp = await Http.PostAsync(Endpoint, body);
                return JObject.Parse(await resp.Content.ReadAsStringAsync());
            }
            catch (Exception ex)
            {
                return new JObject { ["success"] = false, ["error"] = ex.Message };
            }
        }

        /// <summary>One-liner: build envelope + send.</summary>
        public static Task<JObject> Dispatch(string intent, string act, JObject payload,
            string source = "MAMA", string target = "CONTROL")
            => Send(Envelope(intent, act, payload, source, target));

        /// <summary>Health check — is CONTROL alive?</summary>
        public static async Task<bool> IsAlive()
        {
            try
            {
                var r = await Http.GetAsync("http://127.0.0.1:5050/health");
                var j = JObject.Parse(await r.Content.ReadAsStringAsync());
                return j.Value<bool>("control_loaded");
            }
            catch { return false; }
        }
    }
}
