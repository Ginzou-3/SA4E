package com.example.xmaswishes.camel;

import org.apache.camel.builder.RouteBuilder;
import org.springframework.stereotype.Component;

/**
 * Camel route that monitors /data/scans for new files (scanned letters).
 * After "parsing" (placeholder), it sends a POST request to the XmasWishes API.
 */
@Component
public class ScanToXmasWishesRoute extends RouteBuilder {

    @Override
    public void configure() throws Exception {

        from("file:C:/Users/kraem/OneDrive/Universität/Master-Zeit/1.Semester/EBS/SA4E/Uebung_2/src/main/java/com/example/xmaswishes/camel/data?move=/done")
                .routeId("ScanToXmasWishesRoute")
                // 1) "Scan" or parse the file -> in a real scenario, do OCR or PDF parsing
                .process(exchange -> {
                    String fileName = exchange.getIn().getHeader("CamelFileName", String.class);
                    String extractedName = "Max Mustermann (from: " + fileName + ")";
                    String extractedWish = "I want a brand new bicycle!";

                    // Create your WishDTO in the message body
                    WishDTO dto = new WishDTO(extractedName, extractedWish, 1);
                    exchange.getIn().setBody(dto);
                })
                // 1) Convert WishDTO -> JSON string using Jackson
                .marshal().json()  // or .marshal().json(JsonLibrary.Jackson)

                // 2) Set content-type header so the remote XmasWishes service reads JSON
                .setHeader("Content-Type", constant("application/json"))

                // 3) Make a POST request to the XmasWishes endpoint
                .to("rest:post:api/wishes?host=http://localhost:8080");
    }

    /**
     * Simple DTO for sending to XmasWishes.
     * Camel can convert it to JSON automatically if the camel-jackson-starter is present.
     */
    static class WishDTO {
        private String personName;
        private String wishText;
        private int status;

        public WishDTO() {}
        public WishDTO(String personName, String wishText, int status) {
            this.personName = personName;
            this.wishText = wishText;
            this.status = status;
        }
        // Getters/Setters...
        public String getPersonName() { return personName; }
        public void setPersonName(String personName) { this.personName = personName; }

        public String getWishText() { return wishText; }
        public void setWishText(String wishText) { this.wishText = wishText; }

        public int getStatus() { return status; }
        public void setStatus(int status) { this.status = status; }
    }
}

