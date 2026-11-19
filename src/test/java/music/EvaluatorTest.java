package music;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public final class EvaluatorTest {
    public static void main(String[] args) {
        List<Track> tracks = List.of(
                new Track("a", "A", "Another Artist", "folk"),
                new Track("b", "B", "Another Artist", "folk"),
                new Track("y", "Y", "Shared Artist", "jazz"),
                new Track("z", "Z", "Shared Artist", "jazz"));
        List<Listening> history = List.of(new Listening("maya", "y", 7),
                new Listening("maya", "z", 9), new Listening("theo", "a", 1));
        MusicData data = new MusicData(tracks, history);

        // Either held-out jazz song matches Maya's training track. Only A has
        // remaining plays among unseen songs, and B wins the zero-play tie.
        check(new Evaluator.Report(1, 1, 1, 0, 0), Evaluator.evaluate(data, 1));
        check(new Evaluator.Report(1, 1, 1, 1, 1.0 / 3), Evaluator.evaluate(data, 3));

        var reversed = new ArrayList<>(history);
        Collections.reverse(reversed);
        check(Evaluator.evaluate(data, 3), Evaluator.evaluate(new MusicData(tracks, reversed), 3));

        MusicData single = new MusicData(tracks, List.of(new Listening("maya", "z", 7)));
        check(new Evaluator.Report(0, 0, 0, 0, 0), Evaluator.evaluate(single, 3));
        try {
            Evaluator.evaluate(data, 0);
            throw new AssertionError("Expected a positive-limit check");
        } catch (IllegalArgumentException expected) {
            // Expected.
        }
    }

    private static void check(Evaluator.Report expected, Evaluator.Report actual) {
        if (!expected.equals(actual)) {
            throw new AssertionError("Expected " + expected + ", got " + actual);
        }
    }
}
