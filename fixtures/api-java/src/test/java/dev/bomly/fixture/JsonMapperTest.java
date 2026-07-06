package dev.bomly.fixture;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.List;

import org.junit.jupiter.api.Test;

class JsonMapperTest {

    private final JsonMapper mapper = new JsonMapper();

    @Test
    void serializesBookmarks() {
        String json = mapper.toJson(List.of(new Bookmark("Docs", "https://docs.example.com")));
        assertEquals("[{\"title\":\"Docs\",\"url\":\"https://docs.example.com\"}]", json);
    }

    @Test
    void roundTrips() {
        List<Bookmark> in = List.of(
                new Bookmark("Docs", "https://docs.example.com"),
                new Bookmark("Status", "https://status.example.com"));
        List<Bookmark> out = mapper.fromJson(mapper.toJson(in));
        assertEquals(in, out);
    }
}
