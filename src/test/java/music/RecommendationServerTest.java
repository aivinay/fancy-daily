package music;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Path;

public final class RecommendationServerTest {
    public static void main(String[] args) throws Exception {
        var model = new Recommender(MusicData.load(Path.of("examples/tracks.tsv"), Path.of("examples/listens.tsv")));
        var server = RecommendationServer.start(model, 0, 5);
        try {
            var uri = URI.create("http://127.0.0.1:" + server.getAddress().getPort()
                    + "/recommendations?user=maya&limit=1");
            var response = HttpClient.newHttpClient().send(HttpRequest.newBuilder(uri).build(),
                    HttpResponse.BodyHandlers.ofString());
            var pick = model.recommend("maya", 1).get(0);
            var track = pick.track();
            String expected = """
                    {"recommendations":[{"id":"%s","title":"%s","artist":"%s","genre":"%s","score":%s,"explanation":"%s"}]}"""
                    .formatted(track.id(), track.title(), track.artist(), track.genre(), pick.score(), pick.reason());
            if (response.statusCode() != 200 || !expected.equals(response.body())) {
                throw new AssertionError("Unexpected response: " + response);
            }
        } finally {
            server.stop(0);
        }
    }
}
