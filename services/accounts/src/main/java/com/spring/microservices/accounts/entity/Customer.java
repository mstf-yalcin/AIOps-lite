package com.spring.microservices.accounts.entity;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Entity;
import jakarta.persistence.OneToOne;
import lombok.*;

@Entity
@Data
@EqualsAndHashCode(callSuper = true)
@AllArgsConstructor
@NoArgsConstructor
@ToString(exclude = "accounts")
public class Customer extends BaseEntity {

    //customerId
    private String name;

    private String email;

    private String mobileNumber;


    @OneToOne(mappedBy = "customer", cascade = {CascadeType.MERGE, CascadeType.PERSIST, CascadeType.REMOVE})
    private Accounts accounts;

    public Customer(String name, String email, String mobileNumber) {
        this.name = name;
        this.email = email;
        this.mobileNumber = mobileNumber;
    }
}
