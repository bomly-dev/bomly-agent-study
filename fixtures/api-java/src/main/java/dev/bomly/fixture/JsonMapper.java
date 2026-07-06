package dev.bomly.fixture;

import java.util.List;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

/** Serialize/deserialize bookmarks with jackson-databind. */
public final class JsonMapper {

    private final ObjectMapper mapper = new ObjectMapper();

    public String toJson(List<Bookmark> bookmarks) {
        try {
            return mapper.writeValueAsString(bookmarks);
        } catch (Exception e) {
            throw new RuntimeException("serialize failed", e);
        }
    }

    public List<Bookmark> fromJson(String json) {
        try {
            return mapper.readValue(json, new TypeReference<List<Bookmark>>() {});
        } catch (Exception e) {
            throw new RuntimeException("deserialize failed", e);
        }
    }
}
