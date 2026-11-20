package music;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Path;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

public final class RecommendationServerTest {
    public static void main(String[] args) throws Exception {
        var model = new Recommender(MusicData.load(Path.of("examples/tracks.tsv"), Path.of("examples/listens.tsv")));
        try (var server = RecommendationServer.start(model, 0, 5)) {
            var client = HttpClient.newHttpClient();
            var maya = request(client, server.port(), "maya");
            var theo = request(client, server.port(), "theo");
            assertPick(maya.get(10, TimeUnit.SECONDS), model.recommend("maya", 1).get(0));
            assertPick(theo.get(10, TimeUnit.SECONDS), model.recommend("theo", 1).get(0));
        }
    }

    private static CompletableFuture<HttpResponse<String>> request(HttpClient client, int port, String listener) {
        var uri = URI.create("http://127.0.0.1:" + port + "/recommendations?user=" + listener + "&limit=1");
        return client.sendAsync(HttpRequest.newBuilder(uri).build(), HttpResponse.BodyHandlers.ofString());
    }

    private static void assertPick(HttpResponse<String> response, Recommender.Recommendation pick) {
        var track = pick.track();
        String expected = """
                {"recommendations":[{"id":"%s","title":"%s","artist":"%s","genre":"%s","score":%s,"explanation":"%s"}]}"""
                .formatted(track.id(), track.title(), track.artist(), track.genre(), pick.score(), pick.reason());
        if (response.statusCode() != 200 || !expected.equals(response.body())) {
            throw new AssertionError("Unexpected response: " + response);
        }
    }
}
