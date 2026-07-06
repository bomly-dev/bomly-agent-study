package dev.bomly.fixture;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class ConfigLoaderTest {

    @Test
    void interpolatesReferences() {
        ConfigLoader cfg = new ConfigLoader();
        // Exercises commons-text interpolation through commons-configuration2.
        assertEquals("https://bookmarks.example.com/api", cfg.resolve("baseUrl"));
    }

    @Test
    void interpolatesOverriddenValues() {
        ConfigLoader cfg = new ConfigLoader();
        cfg.set("host", "internal.example.net");
        assertEquals("https://internal.example.net/api", cfg.resolve("baseUrl"));
    }
}
