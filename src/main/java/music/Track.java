package music;

/** A catalog entry identified by a stable track ID. */
public record Track(String id, String title, String artist, String genre) {
    public Track {
        if (id == null || id.isBlank() || title == null || title.isBlank()
                || artist == null || artist.isBlank() || genre == null || genre.isBlank()) {
            throw new IllegalArgumentException("Track ID, title, artist and genre are required");
        }
    }
}
