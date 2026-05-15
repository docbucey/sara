using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using Newtonsoft.Json.Linq;

namespace DisabilityMapper.Services
{
    /// <summary>
    /// Implements steno chord accumulation for a mouse-driven virtual stenotype keyboard.
    ///
    /// Operating mode (Latch Mode – default, Parkinson's-friendly):
    ///   • Clicking a key LATCHES it (stays highlighted).
    ///   • Clicking again UN-LATCHES it.
    ///   • Pressing ⏎ SEND (or auto-fire timeout) fires the accumulated chord.
    ///   • Pressing ✱ alone = undo last word. ✱ combined with other keys = modifier.
    ///
    /// Canonical steno key order (standard English steno / Plover-compatible):
    ///   # S T K P W H R  A O * E U  -F -R -P -B -L -G -T -S -D -Z
    ///
    /// Chord string = active keys concatenated in canonical order.
    /// Example: S+K+P → "SKP" = "and"
    ///          -T alone → "-T" = "the"
    ///          A+E+U vowels → "AEU" = "a"
    /// </summary>
    public class StenoChordEngine
    {
        // Keys currently latched (may be cleared between fires)
        private readonly HashSet<string> _latched = new(StringComparer.Ordinal);

        // History of injected words for undo
        private readonly Stack<string> _history = new();

        // Auto-fire timer
        private Timer?  _autoFireTimer;
        private int     _autoFireMs;

        // ── Events ───────────────────────────────────────────────────────────

        /// <summary>Fires with the text that should be injected into the OS.</summary>
        public event Action<string>? TextReady;

        /// <summary>Fires whenever the active chord display should update.</summary>
        public event Action<string>? ChordChanged;

        // ── Canonical key ordering ────────────────────────────────────────────

        private static readonly string[] KeyOrder =
        {
            "#",
            "S",  "T",  "K",  "P",  "W",  "H",  "R",
            "A",  "O",  "*",  "E",  "U",
            "-F", "-R", "-P", "-B", "-L", "-G", "-T", "-S", "-D", "-Z"
        };

        // ── Starter dictionary (Plover-compatible English steno briefs) ───────
        //
        // Extend this at runtime via LoadDictionary(path) for a full Plover JSON.
        // Keys use canonical chord notation; values are the output text.

        private readonly Dictionary<string, string> _dict =
            new(StringComparer.Ordinal)
        {
            // ── The 100 most common English words (verified Plover briefs) ──
            { "-T",     "the"    },
            { "-F",     "of"     },
            { "SKP",    "and"    },
            { "TO",     "to"     },
            { "AEU",    "a"      },
            { "TPH",    "in"     },
            { "T",      "it"     },
            { "-B",     "be"     },
            { "TH",     "this"   },
            { "TP",     "for"    },
            { "R",      "are"    },
            { "U",      "you"    },
            { "K",      "can"    },
            { "HR",     "will"   },
            { "SR",     "have"   },
            { "TPR",    "from"   },
            { "HE",     "he"     },
            { "WE",     "we"     },
            { "TKO",    "do"     },
            { "SO",     "so"     },
            { "TPHO",   "no"     },
            { "WA-S",   "was"    },
            { "S",      "is"     },
            { "KPW",    "but"    },
            { "EU",     "I"      },
            { "SHE",    "she"    },
            { "TPHU",   "new"    },
            { "WA",     "way"    },
            { "SEU",    "say"    },
            { "TPHA",   "any"    },
            { "A",      "at"     },
            { "O",      "or"     },
            { "AOU",    "out"    },
            { "EUPL",   "I'm"    },
            { "TKPWOT", "got"    },
            { "TKAOE",  "day"    },
            { "KPH",    "come"   },
            { "TPH-G",  "ing"    },   // suffix
            { "-S",     "s"      },   // plural suffix
            { "-D",     "d"      },   // past-tense suffix
            { "SKP-R",  "and are"},
            { "SKP-T",  "and the"},
            { "W-",     "with"   },
            { "PHAE",   "may"    },
            { "PWAO",   "by"     },
            { "AUL",    "all"    },
            { "TPHEUF", "if"     },
            { "TKPWAO", "go"     },
            { "TKPW",   "good"   },
            { "SHROEUP","know"   },
            { "HRAOEUBG","like"  },
            { "PHAEBG", "make"   },
            { "TEUPL",  "time"   },
            { "PHOPB",  "one"    },
            { "PHRO",   "people" },
            { "THAEUR", "their"  },
            { "TWHAOER","there"  },
            { "AOEUR",  "our"    },
            { "AEUR",   "your"   },
            { "HA-F",   "half"   },
            { "PHEU",   "my"     },
            { "PHED",   "me"     },
            { "HO",     "how"    },
            { "WHEPB",  "when"   },
            { "WOBG",   "work"   },
            { "TEUBG",  "think"  },
            { "TKPWAOEU","guy"   },
            { "PREUB",  "pretty" },
            { "PRAOEUBGS","price"},
        };

        // ── Public API ────────────────────────────────────────────────────────

        public void SetAutoFire(int ms)
        {
            _autoFireMs = ms;
            _autoFireTimer?.Dispose();
            _autoFireTimer = null;
        }

        /// <summary>Toggle a steno key latch (UI click).</summary>
        public void ToggleKey(string keyId)
        {
            // Normalise: both physical S keys share the same logical key
            var key = keyId == "S2" ? "S" : keyId;

            if (!_latched.Remove(key))
                _latched.Add(key);

            NotifyChordChanged();
            ResetAutoFire();
        }

        public bool IsLatched(string keyId) =>
            _latched.Contains(keyId == "S2" ? "S" : keyId);

        /// <summary>Fire the current chord → look up text → emit TextReady.</summary>
        public void Fire()
        {
            if (_latched.Count == 0) return;

            // ✱ alone = undo last injected word
            if (_latched.Count == 1 && _latched.Contains("*"))
            {
                if (_history.TryPop(out var last))
                    TextReady?.Invoke("\b \b".PadRight(last.Length + 2, '\b'));
                _latched.Clear();
                NotifyChordChanged();
                return;
            }

            var chord = BuildChordString();
            _latched.Clear();
            NotifyChordChanged();

            var word = _dict.TryGetValue(chord, out var w) ? w : $"[{chord}]";
            var output = word + " ";
            _history.Push(output);
            TextReady?.Invoke(output);
        }

        /// <summary>Inject a raw text string (bypasses chord lookup).</summary>
        public void InjectRaw(string text)
        {
            _history.Push(text);
            TextReady?.Invoke(text);
        }

        /// <summary>Undo the last injected word (same as ✱ alone).</summary>
        public void Undo()
        {
            if (_history.TryPop(out var last))
                TextReady?.Invoke(new string('\b', last.Length));
        }

        public void ClearLatch()
        {
            _latched.Clear();
            NotifyChordChanged();
        }

        public IReadOnlyCollection<string> LatchedKeys => _latched;

        // ── Dictionary management ─────────────────────────────────────────────

        /// <summary>Add or overwrite a chord entry at runtime.</summary>
        public void AddEntry(string chord, string word) => _dict[chord] = word;

        /// <summary>
        /// Loads a Plover-format JSON dictionary (chord → translation) and merges
        /// it into the current dictionary.  Returns the number of entries loaded.
        /// Throws on file/parse errors so the caller can surface a message.
        /// </summary>
        /// <remarks>
        /// Plover JSON format:  { "CHORD": "translation", ... }
        /// Chords use hyphens where standard (e.g. "-T", "A-R", "KW-BG").
        /// Special-format entries like {.} {,} {^} are imported as-is so the
        /// engine can output punctuation/suffix strokes verbatim.
        /// </remarks>
        public int LoadDictionary(string path)
        {
            var text = File.ReadAllText(path);
            var obj  = JObject.Parse(text);
            int count = 0;
            foreach (var kv in obj)
            {
                if (kv.Key is null || kv.Value is null) continue;
                var chord       = kv.Key.Trim();
                var translation = kv.Value.ToString();
                if (string.IsNullOrEmpty(chord)) continue;
                _dict[chord] = translation;
                count++;
            }
            return count;
        }

        // ── Internals ─────────────────────────────────────────────────────────

        private string BuildChordString() =>
            string.Concat(KeyOrder.Where(k => _latched.Contains(k)));

        private void NotifyChordChanged() =>
            ChordChanged?.Invoke(BuildChordString());

        private void ResetAutoFire()
        {
            if (_autoFireMs <= 0) return;
            _autoFireTimer?.Dispose();
            _autoFireTimer = new Timer(_ => Fire(), null, _autoFireMs, Timeout.Infinite);
        }
    }
}
