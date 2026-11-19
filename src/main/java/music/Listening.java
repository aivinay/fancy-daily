package music;

/** One listener's total plays for one track. */
public record Listening(String userId, String trackId, int plays) {
    public Listening {
        if (userId == null || userId.isBlank() || trackId == null || trackId.isBlank()) {
            throw new IllegalArgumentException("User ID and track ID are required");
        }
        if (plays <= 0) {
            throw new IllegalArgumentException("Expected a positive play count, found " + plays);
        }
    }
}
