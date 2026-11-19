package music;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import java.util.TreeMap;

/** Reproducible leave-one-track-out evaluation on aggregated listening histories. */
public final class Evaluator {
    private Evaluator() {}

    public record Report(int listeners, double hitRate, double meanReciprocalRank,
                         double popularityHitRate, double popularityMeanReciprocalRank) {}

    public static Report evaluate(MusicData data, int limit) {
        if (limit < 1) {
            throw new IllegalArgumentException("limit must be positive");
        }
        Map<String, String> heldOut = selectHoldouts(data.history());
        int listeners = heldOut.size();
        if (listeners == 0) {
            return new Report(0, 0, 0, 0, 0);
        }

        List<Listening> training = new ArrayList<>();
        Map<String, Set<String>> heard = new HashMap<>();
        Map<String, Long> playCounts = new HashMap<>();
        for (Listening row : data.history()) {
            if (row.trackId().equals(heldOut.get(row.userId()))) {
                continue;
            }
            training.add(row);
            heard.computeIfAbsent(row.userId(), key -> new HashSet<>()).add(row.trackId());
            playCounts.merge(row.trackId(), (long) row.plays(), Long::sum);
        }

        Recommender recommender = new Recommender(new MusicData(data.tracks(), training));
        List<String> popular = data.tracks().stream().map(Track::id)
                .sorted(Comparator.<String>comparingLong(id -> playCounts.getOrDefault(id, 0L))
                        .reversed().thenComparing(Comparator.naturalOrder()))
                .toList();

        Tally personalized = new Tally();
        Tally baseline = new Tally();
        for (var entry : heldOut.entrySet()) {
            String user = entry.getKey();
            String target = entry.getValue();
            personalized.add(target, recommender.recommend(user, limit).stream()
                    .map(pick -> pick.track().id()).toList());
            Set<String> excluded = heard.get(user);
            baseline.add(target, popular.stream()
                    .filter(id -> !excluded.contains(id)).limit(limit).toList());
        }
        return new Report(listeners, (double) personalized.hits / listeners,
                personalized.reciprocalRanks / listeners, (double) baseline.hits / listeners,
                baseline.reciprocalRanks / listeners);
    }

    private static Map<String, String> selectHoldouts(List<Listening> history) {
        Map<String, List<String>> byUser = new HashMap<>();
        for (Listening row : history) {
            byUser.computeIfAbsent(row.userId(), key -> new ArrayList<>()).add(row.trackId());
        }
        Map<String, String> heldOut = new TreeMap<>();
        for (var entry : byUser.entrySet()) {
            List<String> ids = entry.getValue();
            if (ids.size() >= 2) {
                ids.sort(Comparator.naturalOrder());
                String user = entry.getKey();
                int index = new Random(user.hashCode()).nextInt(ids.size());
                heldOut.put(user, ids.get(index));
            }
        }
        return heldOut;
    }

    private static final class Tally {
        int hits;
        double reciprocalRanks;

        void add(String target, List<String> ranking) {
            int index = ranking.indexOf(target);
            if (index >= 0) {
                hits++;
                reciprocalRanks += 1.0 / (index + 1);
            }
        }
    }
}
