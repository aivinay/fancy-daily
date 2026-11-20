package music;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

public final class RecommendationServerTest {
    public static void main(String[] args) throws Exception {
        var model = new Recommender(MusicData.load(Path.of("examples/tracks.tsv"), Path.of("examples/listens.tsv")));
        try (var server = RecommendationServer.start(model, 0, 5)) {
            var client = HttpClient.newHttpClient();
            var maya = request(client, server.port(), "?user=maya&limit=1");
            var theo = request(client, server.port(), "?user=theo&limit=1");
            assertPick(maya.get(10, TimeUnit.SECONDS), model.recommend("maya", 1).get(0));
            assertPick(theo.get(10, TimeUnit.SECONDS), model.recommend("theo", 1).get(0));

            for (String query : new String[]{"", "?limit=1", "?user=", "?user=%20"}) {
                assertBadRequest(client, server.port(), query, "User ID must not be blank");
            }
            for (String limit : new String[]{"0", "-1"}) {
                assertBadRequest(client, server.port(), "?user=maya&limit=" + limit, "Limit must be at least 1");
            }
            for (String limit : new String[]{"", "three", "2147483648"}) {
                assertBadRequest(client, server.port(), "?user=maya&limit=" + limit, "limit requires a positive integer");
            }
        }
        assertEscapedTitle();
    }

    private static void assertEscapedTitle() throws Exception {
        var track = new Track("t1", "Café \"Live\" \\ Encore", "Artist", "Jazz");
        var model = new Recommender(new MusicData(List.of(track), List.of()));
        try (var server = RecommendationServer.start(model, 0, 1)) {
            var response = request(HttpClient.newHttpClient(), server.port(), "?user=new")
                    .get(10, TimeUnit.SECONDS);
            String expectedTitle = "\"title\":\"Café \\\"Live\\\" \\\\ Encore\"";
            if (response.statusCode() != 200 || !response.body().contains(expectedTitle)) {
                throw new AssertionError("Unexpected JSON title in " + response.body());
            }
        }
    }

    private static CompletableFuture<HttpResponse<String>> request(HttpClient client, int port, String query) {
        var uri = URI.create("http://127.0.0.1:" + port + "/recommendations" + query);
        return client.sendAsync(HttpRequest.newBuilder(uri).build(), HttpResponse.BodyHandlers.ofString());
    }

    private static void assertBadRequest(HttpClient client, int port, String query, String message) throws Exception {
        var response = request(client, port, query).get(10, TimeUnit.SECONDS);
        String mediaType = response.headers().firstValue("Content-Type").orElse("").split(";", 2)[0];
        String expected = "{\"error\":\"" + message + "\"}";
        if (response.statusCode() != 400 || !mediaType.equalsIgnoreCase("application/json")
                || !expected.equals(response.body())) {
            throw new AssertionError("Unexpected error response for " + query + ": " + response + " " + response.body());
        }
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
