package com.example.xmaswishes.model;

import javax.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "wishes")
public class Wish {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String personName;
    private String wishText;

    // 1 = formulated, 2 = in progress, 3 = delivering, 4 = delivered
    private int status;

    private Instant createdAt;
    private Instant updatedAt;

    public Wish() {}

    // getters & setters
    public Long getId() { return id; }
    public String getPersonName() { return personName; }
    public void setPersonName(String personName) { this.personName = personName; }

    public String getWishText() { return wishText; }
    public void setWishText(String wishText) { this.wishText = wishText; }

    public int getStatus() { return status; }
    public void setStatus(int status) { this.status = status; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }

    public Instant getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(Instant updatedAt) { this.updatedAt = updatedAt; }
}