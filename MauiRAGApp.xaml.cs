using Newtonsoft.Json;
using System.Reflection;
using System.Text;

namespace MauiRAGApp;

public partial class MainPage : ContentPage
{
    private List<KBEntry> _knowledgeBase;

    public MainPage()
    {
        InitializeComponent();
        LoadKnowledgeBase();
    }

    private void LoadKnowledgeBase()
    {
        var assembly = Assembly.GetExecutingAssembly();
        var stream = assembly.GetManifestResourceStream("MauiRAGApp.Resources.Raw.data.json");
        using var reader = new StreamReader(stream);
        var json = reader.ReadToEnd();
        _knowledgeBase = JsonConvert.DeserializeObject<List<KBEntry>>(json);
    }

    private async void OnSendClicked(object sender, EventArgs e)
    {
        var question = UserInput.Text;
        AppendToChat($"You: {question}");

        var context = RetrieveRelevantContext(question);
        var response = await GenerateAnswerFromOpenAI(question, context);

        AppendToChat($"Bot: {response}");
        UserInput.Text = "";
    }

    private string RetrieveRelevantContext(string userQuestion)
    {
        var bestMatch = _knowledgeBase
            .OrderByDescending(kb => ComputeKeywordMatch(kb.Question, userQuestion))
            .FirstOrDefault();

        return bestMatch != null ? bestMatch.Answer : "No matching context found.";
    }

    private double ComputeKeywordMatch(string a, string b)
    {
        var aWords = a.ToLower().Split(' ');
        var bWords = b.ToLower().Split(' ');
        return aWords.Intersect(bWords).Count();
    }

    private async Task<string> GenerateAnswerFromOpenAI(string question, string context)
    {
        using var client = new HttpClient();
        client.DefaultRequestHeaders.Add("Authorization", "Bearer sk-<your-api-key>");

        var payload = new
        {
            model = "gpt-3.5-turbo",
            messages = new[]
            {
                new { role = "system", content = $"Use this context to answer questions: {context}" },
                new { role = "user", content = question }
            }
        };

        var content = new StringContent(JsonConvert.SerializeObject(payload), Encoding.UTF8, "application/json");
        var response = await client.PostAsync("https://api.openai.com/v1/chat/completions", content);
        var resultJson = await response.Content.ReadAsStringAsync();

        dynamic result = JsonConvert.DeserializeObject(resultJson);
        return result?.choices?[0]?.message?.content ?? "No response.";
    }

    private void AppendToChat(string message)
    {
        ChatHistory.Text += $"\n\n{message}";
    }

    public class KBEntry
    {
        public string Question { get; set; }
        public string Answer { get; set; }
    }
}
